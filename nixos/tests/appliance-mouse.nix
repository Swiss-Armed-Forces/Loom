# Point-and-click on the operator's console session.
#
# What this covers is the chain, end to end, because every link in it is
# invisible from either side:
#
#   uinput -> mousedev -> gpm -> loom-console-mouse -> tmux -> the pane
#
# The unit tests under nixos/console-mouse/tests already pin the two halves
# that are pure -- the gpm wire format and the SGR translation. What they
# cannot show is that gpm delivers anything to a client running as the
# operator, that the shim is really in the stream, or that tmux does the
# routing once it is. Those only fail on a booted machine.
#
# The mouse is a uinput device created inside the guest rather than qemu's
# emulated one, and that is not a preference: qemu 11 removed the HMP
# `mouse_move` and `mouse_button` commands, and the NixOS test driver has no
# replacement for them. A `-device usb-mouse` is attached anyway, so that the
# box boots with a real pointing device on it the way a delivered one would.
#
# Positions are reached by slamming the pointer into a corner. gpm applies
# acceleration and its own scaling to relative motion, so walking to a chosen
# cell would be a calibration exercise with a different answer per console
# size; clamping has no such problem, and the assertions then ask tmux which
# pane covers that cell rather than assuming a layout.
{
  pkgs,
  specialArgs,
  applianceModules,
  loomUser,
}:
let
  # Creates a relative pointing device and drives it. Only the pieces this
  # test needs: motion, the left button, and a flush.
  #
  # mousedev picks the new device up in the mixed /dev/input/mice node that gpm
  # already has open, which is the reason console-mouse.nix reads that node
  # rather than a specific event device -- a mouse appearing after boot has to
  # work, because that is how these boxes are actually used.
  fake-mouse = pkgs.writers.writePython3Bin "loom-fake-mouse" { } ''
    import fcntl
    import os
    import struct
    import sys
    import time

    # linux/uinput.h, with UINPUT_IOCTL_BASE == 'U'.
    UI_DEV_CREATE = 0x5501
    UI_DEV_DESTROY = 0x5502
    UI_SET_EVBIT = 0x40045564
    UI_SET_KEYBIT = 0x40045565
    UI_SET_RELBIT = 0x40045566

    EV_SYN = 0
    EV_KEY = 1
    EV_REL = 2
    REL_X = 0
    REL_Y = 1
    BTN_LEFT = 0x110
    SYN_REPORT = 0
    BUS_USB = 3

    # struct input_event: two __kernel_ulong_t of timestamp, then u16, u16,
    # s32. NATIVE sizes -- "@", not "=" -- because this is a kernel ABI: with
    # "=" a Python "L" is four bytes whatever the machine is, which builds a
    # 16-byte event that uinput rejects with EINVAL for being shorter than the
    # 24 it expects. Asserted rather than trusted, since the failure is a bare
    # errno a long way from its cause.
    EVENT = struct.Struct("@LLHHi")
    assert EVENT.size == 24, EVENT.size

    # struct uinput_user_dev: char name[80], struct input_id (4 x u16),
    # u32 ff_effects_max, then four s32[ABS_CNT] with ABS_CNT == 64. Every
    # field is already 4-aligned, so the packed layout and the native one
    # agree here.
    USER_DEV = struct.Struct("=80s4HI" + "64i" * 4)
    assert USER_DEV.size == 1116, USER_DEV.size
    ABS_FIELDS = [0] * 256


    def emit(fd, etype, code, value):
        os.write(fd, EVENT.pack(0, 0, etype, code, value))


    def sync(fd):
        emit(fd, EV_SYN, SYN_REPORT, 0)
        # gpm is a separate process reading a separate device node, so the
        # report has to get all the way there before the next one is sent.
        time.sleep(0.05)


    def create():
        fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
        for code in (EV_KEY, EV_REL):
            fcntl.ioctl(fd, UI_SET_EVBIT, code)
        fcntl.ioctl(fd, UI_SET_KEYBIT, BTN_LEFT)
        for code in (REL_X, REL_Y):
            fcntl.ioctl(fd, UI_SET_RELBIT, code)
        os.write(fd, USER_DEV.pack(
            b"loom-test-mouse", BUS_USB, 1, 1, 1, 0, *ABS_FIELDS
        ))
        fcntl.ioctl(fd, UI_DEV_CREATE, 0)
        # udev has to notice the device and mousedev has to attach it to the
        # mixed node before anything sent here can reach gpm.
        time.sleep(1.0)
        return fd


    def run(fd, argv):
        for command in argv:
            action, _, argument = command.partition(":")
            if action == "move":
                dx, dy = (int(part) for part in argument.split(","))
                # A deliberately huge delta is clamped by gpm at the screen
                # edge, which is how the corners are reached without having
                # to calibrate against gpm's acceleration.
                emit(fd, EV_REL, REL_X, dx)
                emit(fd, EV_REL, REL_Y, dy)
                sync(fd)
            elif action == "click":
                emit(fd, EV_KEY, BTN_LEFT, 1)
                sync(fd)
                emit(fd, EV_KEY, BTN_LEFT, 0)
                sync(fd)
            else:
                raise SystemExit("unknown command: " + command)


    def main(argv):
        fd = create()
        run(fd, argv)
        # Let the last report land before the device vanishes under it.
        time.sleep(0.5)
        fcntl.ioctl(fd, UI_DEV_DESTROY, 0)
        os.close(fd)


    main(sys.argv[1:])
  '';
in
pkgs.testers.runNixOSTest {
  name = "loom-appliance-mouse";

  node.specialArgs = specialArgs;

  nodes.appliance =
    { lib, ... }:
    {
      imports = applianceModules;

      virtualisation.memorySize = 1024;
      virtualisation.diskSize = 2048;

      # A real pointing device on the box, so gpm has something to bind at boot
      # exactly as it would on delivered hardware. The uinput device above is
      # what the test actually drives -- qemu's mouse has nobody to move it.
      virtualisation.qemu.options = [ "-device usb-mouse" ];

      # CONFIG_INPUT_UINPUT is a module on the NixOS kernel, and nothing here
      # would otherwise load it. console-mouse.nix already asks for mousedev.
      boot.kernelModules = [ "uinput" ];

      environment.systemPackages = [ fake-mouse ];

      # The same three the other appliance tests force off: the framework
      # drives networking itself and Loom cannot come up in here anyway.
      services.dnsmasq.enable = lib.mkForce false;
      networking.interfaces = lib.mkForce { };
      systemd.services.loom.wantedBy = lib.mkForce [ ];
    };

  testScript =
    { nodes, ... }:
    ''
      SOCKET = "/run/loom/tmux.sock"

      def tmux(command):
          return appliance.succeed(f"tmux -S {SOCKET} {command}").strip()

      def panes():
          """Every pane as (id, left, top, right, bottom, active, command)."""
          raw = tmux(
              "list-panes -t loom -F "
              "'#{pane_id} #{pane_left} #{pane_top} #{pane_right} "
              "#{pane_bottom} #{pane_active} #{pane_start_command}'"
          )
          out = []
          for line in raw.splitlines():
              pane_id, left, top, right, bottom, active, command = line.split(" ", 6)
              out.append(
                  {
                      "id": pane_id,
                      "left": int(left),
                      "top": int(top),
                      "right": int(right),
                      "bottom": int(bottom),
                      "active": active == "1",
                      "command": command,
                  }
              )
          return out

      def pane_covering(col, row):
          """The pane containing a zero-based console cell, or None."""
          for pane in panes():
              horizontal = pane["left"] <= col <= pane["right"]
              vertical = pane["top"] <= row <= pane["bottom"]
              if horizontal and vertical:
                  return pane
          return None

      def active_pane():
          for pane in panes():
              if pane["active"]:
                  return pane
          raise Exception("no active pane")

      def mouse(*commands):
          appliance.succeed("loom-fake-mouse " + " ".join(commands))

      # Far enough to clamp at any console size this box will ever have.
      FAR = 30000

      appliance.wait_for_unit("multi-user.target")

      with subtest("gpm runs, and survives the console being resized"):
          appliance.wait_for_unit("gpm.service")

          # The ordering that keeps gpm's one-shot console measurement honest.
          # Asserted on the unit rather than observed, because a test VM's
          # console does not go through the four resizes a real panel does --
          # see branding.nix. Getting this wrong clamps the pointer to a
          # fraction of the screen on the box and nowhere else.
          ordering = appliance.succeed("systemctl show --property=After --value gpm.service")
          assert "loom-console-font.service" in ordering, ordering

          # The regression this subtest exists for.
          #
          # loom-console-font-reapply fires from a udev rule when the DRM
          # driver takes the console, and it has to make gpm re-read the size.
          # Signalling it does not work: gpm's SIGWINCH path segfaults, which
          # is unsurprising once you notice nothing ever sends a daemon that
          # signal, so the path is dead code upstream. console-mouse.nix
          # restarts the unit instead -- and the proof is that gpm is still
          # alive after the reapply has run, not that the config says so.
          appliance.wait_until_succeeds(
              "systemctl show --property=Result --value"
              " loom-console-font-reapply.service | grep -qx success"
          )
          appliance.succeed("systemctl is-active gpm.service")
          assert "core-dump" not in appliance.succeed(
              "systemctl show --property=Result --value gpm.service"
          )

          # mousedev, not an evdev node: /dev/input/mice multiplexes every
          # mouse, which is what makes one plugged in after boot work.
          appliance.succeed("test -c /dev/input/mice")

      with subtest("a keypress opens the session, under the shim"):
          fg = appliance.succeed("fgconsole").strip()
          assert fg == "1", f"foreground console is {fg}, not tty1"

          appliance.send_key("ret")
          appliance.wait_until_succeeds("pgrep -u ${loomUser} -f tmux")

          # The shim has to be between the console and the tmux client, not
          # beside it: being in the output stream is the only place the pointer
          # can be drawn without leaving stale cells behind.
          appliance.wait_until_succeeds("pgrep -u ${loomUser} -f loom-console-mouse")

          # Asserted on the client's controlling terminal, which is the
          # observable consequence: without the shim the client sits on
          # /dev/tty1, exactly as this session used to run, and a pts means
          # something allocated a pty and put itself in the middle.
          #
          # The client is identified by asking tmux rather than by pgrep,
          # because the shim's own command line *is* the tmux command line --
          # it was handed `... tmux ... attach-session -t loom` to run -- so
          # any pattern that matches the client matches the shim too, and the
          # shim is legitimately on tty1. It has to be: the ioctl that draws
          # the pointer only works from a process whose controlling terminal
          # is the console it is drawing on.
          appliance.wait_until_succeeds(
              f"tmux -S {SOCKET} list-clients -t loom | grep -q ."
          )
          client = int(tmux("list-clients -t loom -F '#{client_pid}'"))
          terminal = appliance.succeed(f"ps -o tty= -p {client}").strip()
          assert terminal.startswith("pts/"), (
              f"the tmux client is on {terminal}, so nothing is between it "
              "and the console"
          )

      # Wait for the layout to stop moving. `create` respawns panes after the
      # last split, and a click landing mid-respawn would be testing nothing.
      appliance.wait_until_succeeds(
          f"tmux -S {SOCKET} list-panes -t loom | wc -l | grep -qvx 0"
      )

      rows, cols = (
          int(value)
          for value in appliance.succeed("stty size < /dev/tty1").split()
      )

      with subtest("clicking the top-left pane focuses it"):
          mouse(f"move:-{FAR},-{FAR}")
          target = pane_covering(0, 0)
          assert target is not None, panes()
          mouse("click:")
          appliance.wait_until_succeeds(
              f"tmux -S {SOCKET} display -p -t {target['id']} '#{{pane_active}}'"
              " | grep -qx 1"
          )

      with subtest("clicking the top-right pane moves the focus there"):
          # A different pane from the one above, which is what makes this a
          # test of the click rather than of the starting state.
          mouse(f"move:{FAR},0")
          target = pane_covering(cols - 1, 0)
          assert target is not None, panes()
          assert not target["active"], "already focused before the click"
          mouse("click:")
          appliance.wait_until_succeeds(
              f"tmux -S {SOCKET} display -p -t {target['id']} '#{{pane_active}}'"
              " | grep -qx 1"
          )
          assert "btop" in active_pane()["command"], active_pane()

      with subtest("the mouse reaches into a pane, not just onto it"):
          # btop asks for ?1002/?1003/?1006 -- it wants motion as well as
          # clicks -- and tmux only forwards what its own terminal sends it.
          # `mouse_any_flag` is tmux's record of the pane having asked, so a
          # true value here is tmux saying it will route events inward.
          appliance.wait_until_succeeds(
              f"tmux -S {SOCKET} display -p -t {active_pane()['id']}"
              " '#{mouse_any_flag}' | grep -qx 1"
          )

      with subtest("k9s is configured to accept the mouse"):
          # tcell can do every mouse mode, but k9s gates them behind
          # ui.enableMouse, which defaults off -- so without this the pods pane
          # is the one place a click does nothing.
          #
          # Run rather than read off the store, because what matters is the
          # file loom-k9s actually writes. It cannot be observed in the pane
          # here: the log pane only hands over to k9s once the namespace
          # exists, and no cluster ever comes up in a test VM. So the command
          # is invoked directly -- as the operator, or the config directory
          # would end up owned by root -- and killed once it starts waiting for
          # that same cluster. It writes its config before the wait for exactly
          # this kind of reason.
          appliance.succeed(
              "su ${loomUser} -s /bin/sh -c 'timeout 5 loom-k9s' >/dev/null 2>&1"
              " || true"
          )
          config = appliance.succeed("cat /run/loom/k9s/config.yaml")
          assert "enableMouse: true" in config, config

      with subtest("the prefix is unreachable from the keyboard"):
          # `prefix None` rather than `unbind-key -a`, because every mouse
          # behaviour tmux has lives in the root table as an ordinary binding
          # -- unbinding everything would have removed the feature above.
          assert tmux("show-options -g prefix") == "prefix None"
          assert tmux("show-options -g prefix2") == "prefix2 None"

          # And the menus a right-click would otherwise open, which carry
          # Kill, Respawn, Split, New Session and a command prompt.
          root_keys = tmux("list-keys -T root")
          assert "MouseDown3" not in root_keys, root_keys

          # The proof rather than the configuration: Ctrl-b d is what used to
          # detach, and the session must still have its client afterwards.
          appliance.send_key("ctrl-b")
          appliance.send_chars("d")
          appliance.sleep(2)
          attached = tmux("list-clients -t loom | wc -l")
          assert attached != "0", "Ctrl-b d detached the session"

      with subtest("clicking the status line detaches"):
          # The controls are drawn flush against the right-hand edge precisely
          # so that the bottom-right corner of the screen lands inside the
          # detach range -- and so that an operator has the easiest target on
          # the display.
          mouse(f"move:{FAR},{FAR}")
          mouse("click:")
          appliance.wait_until_succeeds(
              f"tmux -S {SOCKET} list-clients -t loom | wc -l | grep -qx 0"
          )

          # Detaching is meant to hand the box back to the banner: the client
          # exits, the shim exits with it, loom-console returns 0 and the login
          # shell leaves, so agetty comes back round.
          appliance.wait_until_succeeds("pgrep -f 'agetty.*tty1'")
    '';
}
