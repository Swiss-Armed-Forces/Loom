"""The Loom appliance installer.

Three programs share this package -- `loom-menu`, `loom-install` and `loom-wipe` --
because they share the part that matters: the device interlock, which is what keeps
the installer from eating the USB stick it is running from or a disk somebody cares
about.

The layout mirrors what each piece is allowed to touch:

    settings.py   what installer.nix baked into this stick, and nothing else
    console.py    everything drawn on the operator's screen
    devices.py    what the box's disks are, and which of them may be written to
    decision.py   whether this boot may install unattended -- pure, and tested
    storage.py    releasing and destroying the pool, shared by install and wipe
    install.py    the install itself
    wipe.py       the erase
    menu.py       the console menu that drives the other two

`devices.py` and `storage.py` reach the outside world through a `CommandRunner`
(`commands.py`) that is passed in rather than imported, so the rules above them can
be exercised against a fake one -- see tests/.
"""
