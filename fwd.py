#!/usr/bin/python

# 2017-01-10 14:21 (Jabbe): created
# 2017-01-10 21:29 (Jabbe): a somewhat more flexible version
# 2017-01-20 16:46 (Jabbe): handle in and outgoing traffic
# 2017-01-24 14:29 (Jabbe): new approach with tuntap devices
# 2017-01-25 15:51 (Jabbe): support for multiple clients

import argparse
import sys
import socket
import select
import time
import os
import tuntap
import ip

BufSize = 2048

class Remote:
    def __init__(self, address):
        self.address = address
        self.lastRx = time.time()
    def __str__(self):
        fmt = "remote [%s]:%d, last rx: %d s ago"
        return fmt % (self.address[0], self.address[1], int(time.time() - self.lastRx))

class Route:
    def __init__(self, prefix, prefixLength, remote):
        self.prefix = prefix
        self.prefixLength = prefixLength
        self.remote = remote
    def __str__(self):
        fmt = "route %s through %s"
        return fmt % (ip.ipv6_prefix_to_str(self.prefix, self.prefixLength), str(self.remote))

def find_remote(remotes, address):
    for r in remotes:
        if r.address == address:
            return r
    return None

def find_route(routes, destination):
    for r in routes:
        if ip.ipv6_prefix_eq(r.prefix, destination, r.prefixLength):
            return r
    return None

def timeout_remotes(remotes, timeout):
    remotes_alive = []
    now = time.time()
    for r in remotes:
        if now >= r.lastRx + timeout:
            print("Timing out remote %s" % str(r))
        else:
            remotes_alive.append(r)
    return remotes_alive

def update_routes(routes, remotes):
    routes_alive = []
    for r in routes:
        if r.remote in remotes:
            routes_alive.append(r)
            continue
        print("  Removing %s" % str(r))
    return routes_alive

def handle_incoming(data, addr, routes, remotes, tun):
    try:
        remote = find_remote(remotes, addr)
        if remote is None:
            remote = Remote(addr)
            remotes.append(remote)
            print("  Got packet from new remote: %s" % (str(remote)))
        remote.lastRx = time.time()
        pi = ip.ipv6_decode(data)
        print("  Packet info: %s" % str(pi))
        route = find_route(routes, pi.source)
        if route is None:
            route = Route(ip.ipv6_prefix(pi.source, 64), 64, remote)
            routes.append(route)
            print("  Added route back to source: %s" % str(route))
        print("  Writing %d B to tun device" % (len(data)))
        os.write(tun, data)
    except Exception as e:
        print("  Error: %s" % e)

def handle_outgoing(data, routes, default, sock):
    try:
        pi = ip.ipv6_decode(data)
        print("  Packet info: %s" % str(pi))
        route = find_route(routes, pi.destination)
        if route is None:
            if not default[0]:
                # In a later version this is the place to generate and send back
                # an ICMP No Route to Destination packet.
                print("  Dropping %d B: No route found and no default route is set" % (len(data)))
                return
            print("  Sending %d B using default route to [%s]:%d" % (len(data), default[0], default[1]))
            addr = default
        else:
            print("  Sending %d B using %s" % (len(data), str(route)))
            addr = route.remote.address
        sock.sendto(data, addr)
    except Exception as e:
        print("  Error: %s" % e)

def listen(local, default, tun, timeout):
    print("Binding local socket to [%s]:%d" % local)
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock.bind(local)

    remotes = []
    routes = []

    while True:
        remotes = timeout_remotes(remotes, timeout)
        routes = update_routes(routes, remotes)

        rlistIn = [sock, tun]
        rlist = select.select(rlistIn, [], [], 5)[0]
        if sock in rlist:
            data, addr = sock.recvfrom(BufSize)
            addr = addr[:2]
            print("Received %d B from [%s]:%d" % (len(data), addr[0], addr[1]))
            handle_incoming(data, addr, routes, remotes, tun)
        elif tun in rlist:
            data = os.read(tun, BufSize)
            print("Received %d B from tun device" % (len(data)))
            handle_outgoing(data, routes, default, sock)

class MyParser(argparse.ArgumentParser):
    def __init__(self, description, extra_help):
        super(MyParser, self).__init__(description=description,
                                       formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        self.extra_help = extra_help

    def print_help(self):
        super(MyParser, self).print_help()
        sys.stderr.write(self.extra_help)

if __name__ == "__main__":
    description = """Forward traffic arrived at a tun device to a remote host
using UDPv6."""

    extra_help = """
# Create a tun device named tun1:
sudo ip tuntap add dev tun1 mode tun

# Bring it up:
sudo ip link set tun1 up

# Route traffic destined to fc02::/64 to it:
sudo sudo ip route add fc02::/64 dev tun1
"""

    parser = MyParser(description, extra_help)

    parser.add_argument("--tun", dest="tun", metavar="TUNDEV",
                        default="tun0",
                        help="Tun device")
    parser.add_argument("--default", dest="default_addr", metavar="DEFAULT",
                        default=None,
                        help="Address to route to per default")
    parser.add_argument("--defaultport", dest="default_port", metavar="DEFAULTPORT",
                        default=56830, type=int,
                        help="Port to route to per default")
    parser.add_argument("--local", dest="local_addr", metavar="LOCAL",
                        default="::",
                        help="Address of the local node")
    parser.add_argument("--localport", dest="local_port", metavar="LOCALPORT",
                        default=56830, type=int,
                        help="Port of the local node")
    parser.add_argument("--timeout", dest="timeout", metavar="TIMEOUT",
                        default=100, type=int,
                        help="Timeout in seconds")

    args = parser.parse_args()

    print("Tun device: %s" % args.tun)
    tun = tuntap.tun_open(args.tun)

    default = (args.default_addr, args.default_port)
    print("Default route is set to [%s]:%d" % default)

    local = (args.local_addr, args.local_port)
    print("Local is set to [%s]:%d" % local)

    print("Timeout is set to %d s" % args.timeout)

    listen(local, default, tun, args.timeout)
