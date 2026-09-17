# Loom branding for everything on screen before Loom itself.
#
# Shared by the appliance and by the installer stick, because an operator meets
# both and they should not look like two different products. What lives here is
# what the two have in common: the name in the boot menu, the logo, and the
# plymouth theme.
#
# What differs stays with the boot path that owns it:
#
#   box-hardware.nix  `quiet`, because the appliance boot has nothing to say
#   modes.nix         `plymouth.enable=0` for first-time setup, which has plenty
#   installer.nix     the UKI splash and the serial-console guard
#
# The appliance boots kernel+initrd through systemd-boot and so has no earlier
# surface than plymouth. The stick boots a UKI, whose stub can draw a bitmap
# before Linux exists at all -- hence `splashBmp` below, which only it uses.
{
  lib,
  pkgs,
  loomSrc,
  ...
}:
let
  # The amber the logo is drawn in (Frontend/public/favicon.svg). Plymouth wants
  # 0xRRGGBB rather than CSS notation.
  loomAmber = "0xf7b718";

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
      --replace-fail 'ProgressBarForegroundColor=0xffffff' 'ProgressBarForegroundColor=${loomAmber}'

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
  };

  config = {
    loom.branding = {
      inherit logoPng splashBmp;
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
