# The WiFi access point

Radios are disabled on every appliance image except one built with `build-appliance-image --wifi`.
**Check `loom-appliance/facts.md` first** — it says whether this box has the access point at all. If it does not,
there is nothing to diagnose here and no way to turn one on from the console; it takes a new stick.

The access point is bridged onto the same segment as the wired port, so a client that associates
gets an address and reaches Loom exactly as a wired client does. The SSID and passphrase are shown
on the login screen — `loom-info` prints them again.

This changes the threat model: the box is no longer reachable only by someone standing at it. See
`## Threat model` in `/home/loom/loom/Documentation/appliance.md`.

## Checking it

```bash
loom-info                                    # the SSID and passphrase on the banner
systemctl status loom-wifi-check             # says so on the console when the AP never came up
systemctl status hostapd
journalctl --unit hostapd --no-pager --lines 100
rfkill list
iw dev
ip --brief address
```

## When the access point is missing

In order:

1. `rfkill list` — the WiFi radio should be unblocked. Every switch registers blocked on every
    image, so an unblocked radio is `loom-rfkill-unblock-wifi`'s doing and that unit is required
    rather than defensive: a radio it did not reach stays blocked and hostapd cannot bring the
    interface up. Everything else stays blocked, including bluetooth.
2. `journalctl --unit hostapd` — hostapd failing to start names the reason.
3. `loom-platform-info` — reports the radios and, critically, **whether the driver advertises AP
    mode at all**. A radio that cannot do AP mode cannot host an access point, and no amount of
    configuration changes that. This is the single most common cause.
4. `systemctl status loom-wifi-bridge-attach` — the AP can be up while the bridge is not, which
    gives clients an association but no address.

A radio that does not support AP mode needs different hardware or a wired connection. It is not
fixable here.

## More

`### The WiFi access point` in `/home/loom/loom/Documentation/appliance.md` covers the build flags
and the credentials; `## Threat model` covers what enabling it changes.
