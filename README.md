# Forwarder

Make it possible for two nodes to communicate on a single UDPv6 link.

This is useful when a Telecom operator is in between the server and
the client. The client (e.g. a cellular phone) must initiate the
communication and all further communication must go between the sender
port and the receiver port.

Known limitations:

- IPv6 is required. It is quite strait forward to improve the tool to
  support other type of links, UDPv4, TCP or whatever.

## Setup the server

The server has a public IPv6 address of 2001::1 and wants
to accept UDPv6 packets on port 56830.

```
# Create a tun device named tun0
sudo ip tuntap add dev tun0 mode tun

# Bring it up:
sudo ip link set tun0 up

# Route traffic destined to fc00::/48 to it:
sudo ip route add fc00::/48 dev tun0

# Start the tool and make it listen on port 56830:
./fwd.py --localport 56830 
```

## Setup a client

A client should have a public IPv6 address. It can host many nodes
which internally should have an address with the fc00::/48 prefix.

This is how to setup the client:

```
# Create a tun device named tun0
sudo ip tuntap add dev tun0 mode tun

# Bring it up:
sudo ip link set tun0 up

# Route traffic destined to server to tun0:
sudo ip route add 2001::1 dev tun0

# Start the tool and give the address of the server to it:
./fwd.py --default 2001::1 --defaultport 56830
```

On the client it should now be possible to ping the server if the
tool is running on each machine:

```
ping6 2001::1
```

The tool running on each machine should log about sent and received
packets.

Good luck!

/Jabbe
