#!/usr/bin/python

# 2017-01-10 14:21 (Jabbe): created
# 2017-01-10 21:29 (Jabbe): a somewhat more flexible version
# 2017-01-20 16:46 (Jabbe): handle in and outgoing traffic

import argparse
import sys
import socket
import select
import time

bufSize = 1800

sockPublic = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
sockInternal = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

def forward(data, source, sockOut, dest, str):
    print("%s: Got %d B from [%s]:%d" % (str, len(data), source[0], source[1]))
    if dest is None:
        print("%s: No remote/local: Dropping %d B" % (str, len(data)))
    sent = sockOut.sendto(data, dest)
    if sent == len(data):
        print("%s: Forwarded %d B to [%s]:%d" % (str, len(data), dest[0], dest[1]))
    else:
        print("Failed to send %d B to [%s]:%d, sendto returned: %d" %
              (len(data), dest[0], dest[1], sent))

def listen(public, internal, defaultRemote, defaultLocal, timeout):    
    print("Binding sockPublic to [%s]:%d" % public)
    sockPublic.bind(public)
    print("Binding sockInternal to [%s]:%d" % internal)
    sockInternal.bind(internal)

    remote = defaultRemote
    local = defaultLocal

    while True:
        rlistIn = [sockPublic, sockInternal]
        rlist = select.select(rlistIn, [], [], timeout)[0]
        if sockPublic in rlist:
            data, addr = sockPublic.recvfrom(bufSize)
            if remote is None or remote[0] != addr[0] or remote[1] != addr[1]:
                remote = addr
                print("Remote node changed: [%s]:%d" % (remote[0], remote[1]))
            forward(data, addr, sockInternal, local, "sockPublic")
        elif sockInternal in rlist:
            data, addr = sockInternal.recvfrom(bufSize)
            if local is None or local[0] != addr[0] or local[1] != addr[1]:
                local = addr
                print("Local node changed: [%s]:%d" % (local[0], local[1]))
            forward(data, addr, sockPublic, remote, "sockInternal")
        else:
            if remote != defaultRemote:
                remote = defaultRemote
                print("Timeout, remote node set to: [%s]:%d", remote)
            if local != defaultLocal:
                local = defaultLocal
                print("Timeout, local node set to: [%s]:%d", local)

if __name__ == "__main__":    
    description = "Forward UDPv6 packets from one address to another."
    
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--public", dest="pub_addr", metavar="PUBADDR",
                        default="::",
                        help="Public address")
    parser.add_argument("--publicport", dest="pub_port", metavar="PUBPORT",
                        default=5683, type=int,
                        help="Public port")
    parser.add_argument("--internal", dest="int_addr", metavar="INTADDR",
                        default="fc00:1::1",
                        help="Internal address",)
    parser.add_argument("--internalport", dest="int_port", metavar="INTPORT",
                        default=5683, type=int,
                        help="Internal port")
    parser.add_argument("--remote", dest="remote_addr", metavar="REMOTE",
                        default=None, 
                        help="Address of the remote node")
    parser.add_argument("--remoteport", dest="remote_port", metavar="REMOTEPORT",
                        default=5683, type=int,
                        help="Port of the remote node")
    parser.add_argument("--local", dest="local_addr", metavar="LOCAL",
                        default=None, 
                        help="Address of the local node")
    parser.add_argument("--localport", dest="local_port", metavar="LOCALPORT",
                        default=5683, type=int,
                        help="Port of the local node")
    parser.add_argument("--timeout", dest="timeout", metavar="TIMEOUT",
                        default=10, type=int,
                        help="Timeout in seconds")

    args = parser.parse_args()

    public = (args.pub_addr, args.pub_port)
    print("Public is set to [%s]:%d" % public)

    internal = (args.int_addr, args.int_port)
    print("Internal is set to [%s]:%d" % internal)

    remote = (args.remote_addr, args.remote_port)
    print("Remote is set to [%s]:%d" % remote)

    local = (args.local_addr, args.local_port)
    print("Local is set to [%s]:%d" % local)

    listen(public, internal, remote, local, args.timeout)
