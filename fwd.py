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

class Session:
    def __init__(self, sock, local, remote):
        self.sock = sock
        self.local = local
        self.remote = remote
        self.lastUsed = time.time()
    def __repr__(self):
        return "local [%s]:%d remote [%s]:%d" % (self.local[0], self.local[0],
                                                 self.remote[0], s.remote[0])

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

def remove_old_sessions(sessions, timeout):
    valid = []
    for s in sessions:
        if time.time() >= s.lastUsed + timeout:
            print("Timing out session %s" % str(s))
            continue
        valid.append(s)
    return valid

def find_session(local, remote, sessions):
    for s in sessions:
        if s.local == local and s.remote == remote:
            return s
    return None

def handle_incoming(data, addr, sessions):
    # TODO
    pass

def handle_outgoing_def(data, addr, defaultRemote, sockPublic):
    forward(data, addr, sockPublic, defaultRemote, 'Default out')

def handle_outgoing(data, addr, session, sockPublic):
    s = find_session(addr, defaultRemote)
    if not s:
        s = Session(sockInternal, addr, defaultRemote)
        sessions.append(s)
    s.lastUsed = time.time()
    pass

def listen(public, internal, defaultRemote, defaultLocal, timeout):
    sessions = []
    defaultSession = None

    sockPublic = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sockInternal = None

    print("Binding sockPublic to [%s]:%d" % public)
    sockPublic.bind(public)

    if defaultRemote[0]:
        print("Binding sockInternal to [%s]:%d" % internal)
        sockInternal = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        sockInternal.bind(internal)

    while True:
        sessions = remove_old_sessions(sessions)
        rlistIn = [sockPublic]
        if sockInternal:
            rListIn.append(sockInternal)
        rlist = select.select(rlistIn, [], [], timeout)[0]

        if sockPublic in rlist:
            data, addr = sockPublic.recvfrom(bufSize)
            handle_incoming(data, addr[:2], sessions)

        if sockInternal and sockInternal in rlist:
            data, addr = sockInternal.recvfrom(bufSize)
            handle_outgoing_def(data, addr[:2], defaultRemote, sockPublic)

        for s in sessions:
            if s.sock in rlist:
                handle_outgoing(data, addr[:2], s)

if __name__ == "__main__":
    description = "Forward UDPv6 packets from one address to another."

    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--public", dest="pub_addr", metavar="PUBADDR",
                        default="::",
                        help="Public address")
    parser.add_argument("--publicport", dest="pub_port", metavar="PUBPORT",
                        default=56830, type=int,
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
                        default=56830, type=int,
                        help="Port of the remote node")
    parser.add_argument("--local", dest="local_addr", metavar="LOCAL",
                        default=None,
                        help="Address of the local node")
    parser.add_argument("--localport", dest="local_port", metavar="LOCALPORT",
                        default=5683, type=int,
                        help="Port of the local node")
    parser.add_argument("--timeout", dest="timeout", metavar="TIMEOUT",
                        default=120, type=int,
                        help="Timeout in seconds")

    args = parser.parse_args()

    if (not args.remote_addr) == (not args.local_addr):
        print("Exactly one of --local and --remote must be specified")
        parser.print_help()
        sys.exit()

    public = (args.pub_addr, args.pub_port)
    print("Public is set to [%s]:%d" % public)

    internal = (args.int_addr, args.int_port)
    print("Internal is set to [%s]:%d" % internal)

    remote = (args.remote_addr, args.remote_port)
    print("Remote is set to [%s]:%d" % remote)

    local = (args.local_addr, args.local_port)
    print("Local is set to [%s]:%d" % local)

    listen(public, internal, remote, local, args.timeout)
