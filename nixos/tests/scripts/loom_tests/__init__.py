"""The appliance's VM tests.

One module per test node under this package, plus the helpers they share. Each
`nixos/tests/*.nix` installs this package into its test driver and calls the `run()` of
the module it belongs to -- see `driver.py` for why the tests live out here at all.
"""
