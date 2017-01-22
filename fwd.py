#!/usr/bin/python

# 2017-01-10 14:21 (Jabbe): created

import argparse
import sys
import socket

thisNode = ("2001::1", 5683)
node1 = ("2001::2", 5683)
node2 = ("2001::3", 5685)

bufSize = 1800

listenSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

def forward(data, toAddr, toPort):
    print("Forwarding: %d B to [%s]:%d using source [%s]:%d" %
          (len(data), toAddr, toPort, thisNode[0], thisNode[1]))
    sent = listenSocket.sendto(data, (toAddr, toPort))
    if sent != len(data):
        print("Failed to send %d B, sendto returned: %d" % (len(data), sent))

def listen():
    print("Binding AF_INET6/UDP to address [%s]:%d" % (thisNode[0], thisNode[1]))
    listenSocket.bind((thisNode[0], thisNode[1]))
    while True:
        data, addr = listenSocket.recvfrom(bufSize)
        print("Got %d B from [%s]:%d" % (len(data), addr[0], addr[1]))        
        if addr[0] == node1[0] and addr[1] == node1[1]:
            forward(data, node2[0], node2[1])
        elif addr[0] == node2[0] and addr[1] == node2[1]:
            forward(data, node1[0], node1[1])
        else:
            print("Dropping %d B from [%s]:%d: Not matching node1 or node2" % 
                  (len(data), addr[0], addr[1]))

listen()