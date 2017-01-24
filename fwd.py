#!/usr/bin/python

# 2017-01-10 14:21 (Jabbe): created
# 2017-01-10 21:29 (Jabbe): a somewhat more flexible version
# 2017-01-20 16:46 (Jabbe): handle in and outgoing traffic
# 2017-01-24 14:29 (Jabbe): new approach with tuntap devices

import argparse
import sys
import socket
import select
import time
import tuntap
import os

BufSize = 2048

def handle_incoming(data, tun):
    print("Writing %d B to tun device" % (len(data)))
    os.write(tun, data)

def handle_outgoing(data, addr, sock):
    if addr[0] is None:
        print("Dropped %d B, remote is not set" % (len(data)))
        return
    print("Sending %d B to remote: [%s]:%d" % (len(data), addr[0], addr[1]))
    sock.sendto(data, addr)

def listen(local, defaultRemote, tun, timeout):
    print("Binding local socket to [%s]:%d" % local)
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock.bind(local)

    remote = defaultRemote
    lastRx = None

    while True:
        rlistIn = [sock, tun]
        rlist = select.select(rlistIn, [], [], 5)[0]
        if sock in rlist:
            data, addr = sock.recvfrom(BufSize)
            lastRx = time.time()
            print("Received %d B from [%s]:%d" % (len(data), addr[0], addr[1]))
            if remote is None or remote[0] != addr[0] or remote[1] != addr[1]:
                remote = addr[:2]
                print("Remote changed: [%s]:%d" % (remote[0], remote[1]))
            handle_incoming(data, tun)
        elif tun in rlist:
            data = os.read(tun, BufSize)
            print("Received %d B from tun device" % (len(data)))
            handle_outgoing(data, remote, sock)
        elif lastRx is not None and time.time() >= lastRx + timeout:
            if remote != defaultRemote:
                remote = defaultRemote
                print("Timeout, remote set to: [%s]:%d" % (remote[0], remote[1]))

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
    parser.add_argument("--remote", dest="remote_addr", metavar="REMOTE",
                        default=None,
                        help="Address of the remote node")
    parser.add_argument("--remoteport", dest="remote_port", metavar="REMOTEPORT",
                        default=56830, type=int,
                        help="Port of the remote node")
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

    remote = (args.remote_addr, args.remote_port)
    print("Remote is set to [%s]:%d" % remote)

    local = (args.local_addr, args.local_port)
    print("Local is set to [%s]:%d" % local)

    print("Timeout is set to %d s" % args.timeout)

    listen(local, remote, tun, args.timeout)
