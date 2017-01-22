#!/usr/bin/python

# 2017-01-10 14:21 (Jabbe): created
# 2017-01-10 21:29 (Jabbe): a somewhat more flexible version

"""
To make it possible to perform outgoing requests to a server on the Internet:

1. Add the from_address (default fc00:1::1) to the node:
   sudo ip addr add fc00:1::1 dev lo

2. Start this tool with the to_address set to the server that runs somewhere on 
   the Internet. 

3. Send the requests to the from_address. This tool will forward the request
   to the server. The response from the server is forwarded back to the address 
   that initiated the request.
"""

import argparse
import sys
import socket
import select

bufSize = 1800

sockFrom = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
sockTo = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

def forward(data, source, sockOut, dest, str):
    print("%s: Got %d B from [%s]:%d" % (str, len(data), source[0], source[1]))
    sent = sockOut.sendto(data, dest)
    if sent == len(data):
        print("%s: Forwarded %d B to [%s]:%d" % (str, len(data), dest[0], dest[1]))
    else:
        print("Failed to send %d B to [%s]:%d, sendto returned: %d" %
              (len(data), dest[0], dest[1], sent))

def listen(from_ep, to_ep):
    print("Binding fromSocket to [%s]:%d" % from_ep)
    sockFrom.bind(from_ep)
    from_peer = None

    while True:
        rlistIn = [sockFrom, sockTo]
        rlist = select.select(rlistIn, [], [])[0]
        if sockFrom in rlist:
            data, addr = sockFrom.recvfrom(bufSize)
            if from_peer is None or from_peer[0] != addr[0] or from_peer[1] != addr[1]:
                print("From peer changed: [%s]:%d" % (addr[0], addr[1]))
                from_peer = addr
            forward(data, addr, sockTo, to_ep, "sockFrom")
        if sockTo in rlist:
            data, addr = sockTo.recvfrom(bufSize)
            forward(data, addr, sockFrom, from_peer, "sockTo")

if __name__ == "__main__":    
    description = "Forward UDPv6 packets from one address to another."
    
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--to", dest="to_addr", metavar="TO",
                        default="2001::1",
                        help="Address to forward requests to")
    parser.add_argument("--toport", dest="to_port", metavar="TO_PORT",
                        default=5683, type=int,
                        help="Port to forward requests to")
    parser.add_argument("--from", dest="from_addr", metavar="FROM",
                        default="fc00:1::1",
                        help="Address to receive requests on",)
    parser.add_argument("--fromport", dest="from_port", metavar="FROM_PORT",
                        default=5683, type=int,
                        help="Port to forward requests from")

    args = parser.parse_args()

    from_ep = (args.from_addr, args.from_port)
    print("From is set to [%s]:%d" % from_ep)

    to_ep = (args.to_addr, args.to_port)
    print("To is set to [%s]:%d" % to_ep)

    listen(from_ep, to_ep)
