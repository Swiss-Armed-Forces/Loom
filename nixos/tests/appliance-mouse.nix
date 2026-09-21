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

  # The driver's own mypy cannot resolve scripts/driver.py, so the type check that
  # runs is the repository's. See the header of that file.
  skipTypeCheck = true;

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

  # The test itself is scripts/appliance_mouse.py, so that the repository's Python
  # hooks reach it -- see scripts/driver.py for why, and for why `skipTypeCheck` is
  # set above.
  testScript = ''
    ${builtins.readFile ./scripts/appliance_mouse.py}

    run(
        appliance,
        start_all=start_all,
        subtest=subtest,
        params=Params(operator="${loomUser}"),
    )
  '';
}
