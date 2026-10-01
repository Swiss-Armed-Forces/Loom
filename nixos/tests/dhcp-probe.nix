# Takes a lease off the appliance and prints what came back with it.
#
# Shared by tests/appliance-wifi.nix, which reads the lease served over the
# bridge, and tests/appliance-dhcp.nix, which reads the one served over the wire.
# The settings behind both are the same block in nixos/network.nix, so a second
# copy of this would only drift.
#
# Deliberately NOT in tests/scripts/loom_tests, which is the *driver's* package:
# nothing here runs on the machine driving the test. It opens an AF_PACKET socket
# on the box's own interface, which only exists inside the guest.
#
# Asking dnsmasq rather than reading its configuration file is the point. The
# bug this guards against was not a missing line: it was the belief that leaving
# option:router out of the configuration left it out of the lease, when dnsmasq
# defaults that option to its own address and only a valueless
# `dhcp-option=option:router` suppresses it (see nixos/network.nix). A test that
# grepped the config would have been written against the same belief and passed
# throughout.
#
# The client is the box itself, on the interface the pool lives on:
# SO_BINDTODEVICE puts the DHCPDISCOVER on that link rather than out of the
# default route, which in a test VM belongs to the framework's own network.
#
# The offer is read off a packet socket rather than off that same UDP socket,
# which is not a detail: dnsmasq answers a broadcast-flagged request by building
# the whole frame and handing it to the interface, so it goes out to the wire and
# never comes back up the local stack. A packet socket sees what the interface
# transmits, which is the thing being asserted anyway -- these are the bytes a
# visitor's laptop receives.
{ pkgs }:
pkgs.writers.writePython3Bin "loom-dhcp-probe" { } ''
  import socket
  import struct
  import sys
  import time

  COOKIE = b"\x63\x82\x53\x63"
  END = 255
  PAD = 0

  # ETH_P_ALL rather than ETH_P_IP, which is the whole reason this works: a
  # packet socket bound to one protocol is fed from the receive path only,
  # and the frame wanted here is one this box is *sending*. Only a tap on
  # everything -- what tcpdump opens -- is handed outgoing frames too.
  ETH_P_ALL = 0x0003
  IPV4 = 4
  IPPROTO_UDP = 17
  SERVER_PORT = 67
  CLIENT_PORT = 68
  SERVER_ID = 54

  # Ours, so a lease being handed to somebody else on the segment is not
  # mistaken for the answer to this request. The box itself is a DHCP client
  # on another network in here, so that traffic is genuinely present.
  XID = 0x10AC0117
  MAC = b"\x02\x00\x6c\x6f\x6f\x6d"

  DEADLINE_S = 10

  # Option 53 DHCPDISCOVER, and a parameter request list (option 55) naming
  # netmask, router and DNS server -- so a router option that is absent below
  # is absent because the server declined to send one, not because nobody
  # asked for it.
  DISCOVER = bytes([53, 1, 1]) + bytes([55, 3, 1, 3, 6]) + bytes([END])

  # op/htype/hlen/hops, xid, secs, flags, 4 addresses, chaddr, sname, file.
  HEADER = struct.Struct("!BBBBIHHIIII16s64s128s4s")


  def request():
      return (
          HEADER.pack(
              1, 1, 6, 0,
              XID,
              0,
              # The broadcast flag: this client has no address yet, so the
              # answer has to go to 255.255.255.255 rather than to the lease
              # it is in the middle of being given.
              0x8000,
              0, 0, 0, 0,
              MAC + b"\x00" * 10,
              b"", b"", COOKIE,
          )
          + DISCOVER
      )


  def options(message):
      found = {}
      body = message[HEADER.size:]
      index = 0
      while index < len(body):
          code = body[index]
          if code == END:
              break
          if code == PAD:
              index += 1
              continue
          length = body[index + 1]
          found[code] = body[index + 2:index + 2 + length]
          index += 2 + length
      return found


  def reply(packet):
      """The DHCP payload of a captured frame, if it answers our request."""
      # Everything on the interface arrives here: ARP, IPv6, our own
      # request. None of it is an error -- it is simply not the answer.
      if len(packet) < 28 or packet[0] >> 4 != IPV4:
          return None
      if packet[9] != IPPROTO_UDP:
          return None
      start = (packet[0] & 0x0F) * 4
      ports = struct.unpack_from("!HH", packet, start)
      if ports != (SERVER_PORT, CLIENT_PORT):
          return None
      body = packet[start + 8:]
      if len(body) < HEADER.size or body[4:8] != struct.pack("!I", XID):
          return None
      return body


  def main():
      interface, server = sys.argv[1], sys.argv[2]

      # Opened before anything is sent, so the answer cannot arrive first.
      sniffer = socket.socket(
          socket.AF_PACKET, socket.SOCK_DGRAM, socket.htons(ETH_P_ALL)
      )
      sniffer.bind((interface, ETH_P_ALL))
      sniffer.settimeout(DEADLINE_S)

      client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
      client.setsockopt(
          socket.SOL_SOCKET, socket.SO_BINDTODEVICE, interface.encode()
      )
      client.bind(("0.0.0.0", CLIENT_PORT))
      client.sendto(request(), ("255.255.255.255", SERVER_PORT))

      deadline = time.monotonic() + DEADLINE_S
      offer = None
      while offer is None and time.monotonic() < deadline:
          # Everything else on the interface -- our own request included --
          # is skipped rather than waited on.
          answer = reply(sniffer.recv(2048))
          if answer is None:
              continue
          # And whoever else is on this segment is skipped too. In the test
          # VM that is qemu's own DHCP server, one bridge port away, which
          # answers this request as readily as the appliance does; on a box
          # it would be a second server somebody plugged in. The lease under
          # test is the one the appliance sent.
          if options(answer).get(SERVER_ID) == socket.inet_aton(server):
              offer = answer

      if offer is None:
          sys.exit(f"no DHCP offer from {server} on {interface}")

      print("yiaddr", socket.inet_ntoa(offer[16:20]))
      for code, value in sorted(options(offer).items()):
          addressy = len(value) == 4 and code in (1, 3, 6, 54)
          shown = socket.inet_ntoa(value) if addressy else value.hex()
          print("option", code, shown)


  main()
''
