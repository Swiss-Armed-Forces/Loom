# Loom branding for everything on screen before Loom itself.
#
# Shared by the appliance and by the installer stick, because an operator meets
# both and they should not look like two different products. What lives here is
# what the two have in common: the name in the boot menu, the logo, the
# plymouth theme, the console rendering of the logo (`loom-eyes`), and the VT
# font that rendering is made of.
#
# What differs stays with the boot path that owns it:
#
#   box-hardware.nix  `quiet`, because the appliance boot has nothing to say
#   modes.nix         `plymouth.enable=0` for first-time setup, which has plenty
#   installer.nix     the UKI splash
#
# The appliance boots kernel+initrd through systemd-boot and so has no earlier
# surface than plymouth. The stick boots a UKI, whose stub can draw a bitmap
# before Linux exists at all -- hence `splashBmp` below, which only it uses.
{
  config,
  lib,
  pkgs,
  loomSrc,
  ...
}:
let
  # The amber the logo is drawn in (Frontend/public/favicon.svg), as bare
  # RRGGBB. Stored without a prefix because the two things that consume it want
  # different ones: plymouth takes 0xRRGGBB, and the VT palette sequence
  # box.nix writes takes the six digits on their own.
  loomAmberRgb = "f7b718";

  # Amber rings on a black disc, which is why the theme below can leave the
  # upstream black background alone.
  logoPng =
    pkgs.runCommand "loom-logo.png"
      {
        src = "${loomSrc}/Frontend/public/web-app-manifest-512x512.png";
      }
      ''
        # `*.png` is filter=lfs (.gitattributes). cicd/build_appliance_image.sh
        # materialises the payloads, but a closure built by hand from a checkout
        # without them would embed the pointer *text file* instead -- and the
        # first sign of that is a box that boots to a blank screen, which is the
        # worst possible place to discover it. Fail here instead.
        magic="$(head --bytes=4 "$src" | od --address-radix=n --format=x1 | tr --delete ' \n')"
        if [ "$magic" != "89504e47" ]; then
          echo "$src is not a PNG (git-lfs payload not materialised?)" >&2
          exit 1
        fi
        cp "$src" $out
      '';

  # systemd-stub renders the UKI's `.splash` section, and its splash.c reads
  # uncompressed BMP only -- BMP3: is that classic 24-bit form. Alpha is
  # flattened onto black rather than dropped, or the disc gains a white square.
  #
  # The stub centres the bitmap without scaling it, so the 512px source is
  # already the right size on a 1080p or a 4K panel.
  splashBmp =
    pkgs.runCommand "loom-splash.bmp"
      {
        nativeBuildInputs = [ pkgs.imagemagick ];
      }
      ''
        magick ${logoPng} -background black -alpha remove -alpha off BMP3:$out
      '';

  # The font every VT draws in, and the reason the eyes below still look like
  # eyes.
  #
  # What this displaces is NOT an 8x16 cell. fbcon picks its built-in font from
  # the framebuffer it is handed, and on a large panel it lands on Terminus
  # 16x32 -- measured on the box: a 2560x1600 framebuffer gives a 160x50 grid,
  # which is 16 by 32 exactly. So the console starts out twice as coarse in each
  # direction as the 8x16 that every worked example on the subject assumes, and
  # a three-pane session with btop in one of them has 160 columns to live in.
  #
  # Cozette is the replacement because its 512 glyphs cover the box drawing tmux
  # frames its panes with and the eighth blocks btop's meters are made of,
  # neither of which the built-in fonts carry in full, and because it ships two
  # sizes that differ in nothing else -- see `loom.consoleFont`.
  #
  # Six pixels is the floor, and the mark is what sets it: `loomEyes` below is
  # drawn from U+2588, U+2584 and U+2580 and nothing else, and most console
  # fonts are missing the half blocks. Terminus `ter-v32n` -- the size everyone
  # reaches for first -- has U+2588 but neither U+2580 nor U+2584, so it would
  # have rendered the banner and the installer menu as rows of holes. That is a
  # thing nobody sees until a box is in front of somebody at a site, so it is
  # asserted here instead, the same way logoPng above refuses an unmaterialised
  # git-lfs pointer.
  #
  # The assertion runs against whichever size is selected, so switching the knob
  # cannot quietly pick a font that drops the mark.
  consoleFontFile =
    {
      small = "cozette6x13";
      large = "cozette12x26";
    }
    .${config.loom.consoleFont};

  consoleFont =
    pkgs.runCommand "loom-console-font"
      {
        nativeBuildInputs = [
          pkgs.kbd # psfgettable
          pkgs.gzip
        ];
        src = "${pkgs.cozette}/share/consolefonts/${consoleFontFile}.psfu";
      }
      ''
        # `zcat --force` because psfgettable reads no compressed font and most
        # of the alternatives ship as .psf.gz. Without it a gzipped font
        # produces an empty table, every codepoint below "goes missing", and
        # the error blames the font for something gzip did. Cozette itself is
        # uncompressed, which --force passes through untouched.
        #
        # psfgettable prints one `0x0df<TAB>U+2580` line per mapping, in
        # lowercase hex -- hence --ignore-case.
        for cp in 2588 2584 2580; do
          if ! zcat --force "$src" | psfgettable - | grep --quiet --ignore-case "U+$cp\b"; then
            echo "$src has no U+$cp, one of the three glyphs loom-eyes draws" >&2
            exit 1
          fi
        done
        cp "$src" $out
      '';

  # The same mark for the consoles that cannot show a PNG: the two eyes it is
  # actually made of, with the surrounding disc dropped because at console
  # resolution nothing of it survives anyway.
  #
  # Half blocks, everywhere, unconditionally. Every screen that draws these is a
  # Linux VT or a pts of one -- the installer menu (installer.nix), `loom-info`
  # via loom-issue.service (box.nix) and the same command re-run in a tmux pane
  # -- and `consoleFont` above is pinned, and checked at build time, precisely
  # so that all three carry the glyphs. The VT is in UTF-8 mode by default, so
  # the capture in /run/issue.d survives agetty untouched.
  #
  # There used to be a second, ASCII pair here, picked by probing the console
  # device, because the issue file is read by whatever getty is running and a
  # serial one would have shown a screen of question marks. The appliance has no
  # serial console any more (platforms/, installer.nix), so the probe only ever
  # chose between one real answer and a worse one.
  #
  # Colour is deliberately NOT applied here, though both consumers now do apply
  # it. Reaching the exact amber on a VT means redefining a palette entry, and
  # that sequence hangs an xterm (console_codes(4)) -- so the decision depends
  # on which console is being written to, which is something only the caller
  # knows. The installer menu makes it in common.sh, the appliance banner in
  # box.nix. One generator, one colour, two places that decide whether the
  # console in front of them can take it.
  #
  # No backslashes, in either the art or anything printed beside it: agetty
  # reads the issue for escapes of its own and would eat them.
  loomEyes = pkgs.writeShellApplication {
    name = "loom-eyes";
    runtimeInputs = [ ];
    text = ''
      eyes=(
          ' ▄████▄    ▄████▄'
          '██▀  ▀██  ██▀  ▀██'
          '██ ▄▄ ██  ██ ▄▄ ██'
          '██▄  ▄██  ██▄  ▄██'
          ' ▀████▀    ▀████▀'
      )

      # Two spaces, matching the indent every other line of `loom-info` and of
      # the installer menu uses.
      printf '  %s\n' "''${eyes[@]}"
    '';
  };

  # Derived from upstream `spinner` rather than written from scratch, for one
  # specific reason: the NixOS module greps the theme's `ModuleName` to decide
  # which plugin to copy into the initrd (plymouth.nix, `plymouth-initrd-plugins`).
  # A hand-written theme naming a plugin that never reaches the initrd boots to
  # a black screen, and only in the initrd -- the kind of bug that shows up on
  # the box and nowhere else.
  loomTheme = pkgs.runCommand "plymouth-theme-loom" { } ''
    dir=$out/share/plymouth/themes/loom
    mkdir --parents "$dir"
    cp ${pkgs.plymouth}/share/plymouth/themes/spinner/*.png "$dir"/
    cp ${logoPng} "$dir"/watermark.png

    # Upstream parks the watermark at the bottom edge (.96), where it reads as a
    # vendor sticker. Centred above the spinner it reads as the product.
    substitute ${pkgs.plymouth}/share/plymouth/themes/spinner/spinner.plymouth \
      "$dir"/loom.plymouth \
      --replace-fail 'Name=Spinner' 'Name=Loom' \
      --replace-fail 'Description=A theme designed by jimmac that features a simple spinner.' \
        'Description=Loom appliance.' \
      --replace-fail 'WatermarkVerticalAlignment=.96' 'WatermarkVerticalAlignment=.38' \
      --replace-fail 'ProgressBarForegroundColor=0xffffff' 'ProgressBarForegroundColor=0x${loomAmberRgb}'

    # Not a --replace-fail: the upstream value embeds plymouth's own store path,
    # so matching it literally would break on every plymouth bump. The grep is
    # the assertion instead -- a theme whose ImageDir still points into the
    # plymouth package would silently show upstream's art, not ours.
    sed --in-place "s|^ImageDir=.*|ImageDir=$dir|" "$dir"/loom.plymouth
    grep --quiet "^ImageDir=$dir$" "$dir"/loom.plymouth

    # The translated names all still say "Spinner", and plymouth picks by
    # locale. Dropping them leaves exactly one name to be wrong.
    sed --in-place '/^Name\[/d' "$dir"/loom.plymouth
  '';
in
{
  options.loom.consoleFont = lib.mkOption {
    type = lib.types.enum [
      "small"
      "large"
    ];
    default = "small";
    description = ''
      How big the console cell is, for every VT on the box and on the stick.

      `small` is cozette6x13, `large` is cozette12x26. Cozette ships these two
      and nothing between them, and they are identical in every respect that is
      not size -- both cover the box drawing, the eighth blocks and the three
      glyphs `loom-eyes` needs -- so this really is only a size choice.

      What it is measured against is the kernel's own pick, which on a large
      panel is Terminus 16x32. On the 2560x1600 panel the appliance was tested
      on:

        kernel default   16x32   160 x  50
        large            12x26   213 x  61
        small             6x13   426 x 123

      Not `console.font` directly, because the value has to survive the
      build-time glyph check in branding.nix rather than be a free string.
    '';
  };

  options.loom.branding = {
    logoPng = lib.mkOption {
      type = lib.types.package;
      internal = true;
      description = ''
        The Loom logo, lifted out of the embedded checkout and checked to be a
        real PNG rather than an unmaterialised git-lfs pointer.
      '';
    };

    splashBmp = lib.mkOption {
      type = lib.types.package;
      internal = true;
      description = ''
        The same logo as an uncompressed BMP, for a UKI's `.splash` section.
        Only `installer.nix` consumes it; the appliance has no stub to draw it.
      '';
    };

    eyes = lib.mkOption {
      type = lib.types.package;
      internal = true;
      description = ''
        `loom-eyes`: the logo reduced to its two eyes, drawn in half blocks.
        The appliance's login banner and the installer menu both print it, so
        the two screens carry the same mark.
      '';
    };

    amberRgb = lib.mkOption {
      type = lib.types.str;
      internal = true;
      description = ''
        The logo's amber as bare RRGGBB, measured off the favicon rather than
        eyeballed.

        An option because three screens paint with it and a second literal is a
        second thing to get wrong: the plymouth theme above, the VT palette
        box.nix redefines for the login banner, and the installer menu.
      '';
    };
  };

  config = {
    loom.branding = {
      inherit logoPng splashBmp;
      eyes = loomEyes;
      amberRgb = loomAmberRgb;
    };

    # Deliberately not `console.earlySetup`. That would carry the font into the
    # initrd, which is earlier still and therefore even more exposed to the
    # reset described below; and the only thing on screen that early is
    # plymouth, which draws the logo as a PNG and never touches the VT font.
    console.font = "${consoleFont}";
    # Not needed for the line above -- a store path in FONT= is handed straight
    # to setfont. This is what additionally puts the font under /etc/kbd, so
    # that an operator on a plain Alt-F2 console can `setfont cozette12x26` and
    # compare sizes by hand without a store path to type.
    console.packages = [ pkgs.cozette ];

    # -------------------------------------------------------------------------
    # Setting the font once is not enough.
    #
    # `systemd-vconsole-setup.service` is DefaultDependencies=no and
    # Before=sysinit.target, so it applies the font before most of the machine
    # exists. Anything that re-initialises the console afterwards throws it away
    # and the kernel's built-in font comes back -- which is exactly what the box
    # showed: /etc/vconsole.conf named cozette6x13, `setfont cozette6x13` on
    # tty2 worked by hand, and the login screen was still rendering at 16x32.
    #
    # Two things here can do that resetting, and this unit is deliberately
    # agnostic between them:
    #
    #   * a DRM driver taking over from simpledrm. fbcon rebinds without
    #     emitting the `ACTION=="add", SUBSYSTEM=="vtconsole"` event that
    #     systemd's own 90-vconsole.rules keys on, so nothing re-applies it.
    #   * plymouth releasing the console when it quits -- which run mode has and
    #     first-time setup does not (modes.nix passes `plymouth.enable=0`).
    #
    # Re-applying once, late, covers both without having to know which.
    # -------------------------------------------------------------------------
    systemd.services.loom-console-font = {
      description = "Re-apply the console font once the display has settled";
      # Same triple as box.nix's loom-issue.service, and for the same reason:
      # getty-pre.target is the hook for "before anything paints a VT", but it
      # is passive, so a user of it has to pull it into the transaction itself.
      #
      # Ordering before the first painted character is not a nicety. Changing
      # the font resizes the VT, so doing this after agetty has drawn the banner
      # would leave a screen of wrapped fragments.
      wantedBy = [ "multi-user.target" ];
      wants = [ "getty-pre.target" ];
      before = [ "getty-pre.target" ];
      # Absent in setup mode, where plymouth is switched off entirely. An After=
      # on a unit that does not exist is a no-op rather than an error, which is
      # what makes one unit serve both modes.
      after = [ "plymouth-quit-wait.service" ];
      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
        # The binary rather than `systemctl restart systemd-vconsole-setup`:
        # restarting another unit from inside a unit means blocking on the job
        # queue this unit is itself in. Running it directly is synchronous, and
        # it still walks every VT -- which a bare `setfont -C /dev/tty1` would
        # not, leaving Alt-F2 through Alt-F6 at the kernel default.
        #
        # `-` because a console that will not take the font must still get a
        # login prompt. On a box with no remote access a wrong-sized font is
        # cosmetic and a missing getty is unrecoverable.
        ExecStart = "-${config.systemd.package}/lib/systemd/systemd-vconsole-setup";
      };
    };

    # Names the systemd-boot entries: NixOS builds each title from this string
    # plus the specialisation name, so the appliance's two modes read `Loom` and
    # `Loom (first-time-setup)`. It also names the stick, whose UKI carries this
    # system's os-release, and sets NAME/PRETTY_NAME there. `system.nixos.distroId`
    # is untouched, so anything matching `ID=nixos` still works.
    system.nixos.distroName = "Loom";

    boot.plymouth = {
      enable = true;
      theme = "loom";
      themePackages = [ loomTheme ];
      # Also lands as /etc/plymouth/logo.png, for themes compiled against
      # PLYMOUTH_LOGO_FILE. Ours is not one, but leaving the NixOS snowflake
      # behind on a Loom appliance would be its own small surprise.
      logo = logoPng;
    };
  };
}
