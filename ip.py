import struct
from socket import inet_ntop
from socket import inet_pton
from socket import AF_INET6

class IPv6Packet:
    def __init__(self, nextHeader, hopLimit, source, destination, payload):
        self.nextHeader = nextHeader
        self.hopLimit = hopLimit
        self.source = source
        self.destination = destination
        self.payload = payload

    def __str__(self):
        fmt = "nextHeader: %d, hopLimit: %d, source: %s, dest: %s, payloadLength: %d"
        return fmt % (self.nextHeader, self.hopLimit, ipv6_to_str(self.source),
                      ipv6_to_str(self.destination), len(self.payload))

def ipv6_decode(data):
    vh = struct.unpack_from("B", data, 0)[0]
    ver = vh >> 4
    if ver != 6:
        raise Exception("Unsupported version: " % ver)
    (length, nh, hl, src, dst) = struct.unpack_from("!HBB16s16s", data, 4)
    payload = data[40:]
    if length != len(payload):
        raise Exception("Payload length mismatch: expected %d B, got %d B" % (length, len(payload)))
    return IPv6Packet(nh, hl, src, dst, payload)

def ipv6_prefix_eq(p1, p2, prefixLength):
    for i in range(0, prefixLength/8):
        if p1[i] != p2[i]:
            return False
    bits = prefixLength % 8
    mask = 0xff << (8-bits)
    return ord(p1[prefixLength/8]) & mask == ord(p2[prefixLength/8]) & mask

def ipv6_prefix(addr, prefixLength):
    prefix = bytearray(16)
    for i in range(0, prefixLength / 8):
        prefix[i] = addr[i]
    bits = prefixLength % 8
    mask = 0xff << (8-bits)
    prefix[prefixLength/8] = ord(addr[prefixLength/8]) & mask
    return bytes(prefix)

def ipv6_prefix_to_str(prefix, prefixLength):
    return "%s/%d" % (ipv6_to_str(prefix), prefixLength)

def ipv6_to_str(addr):
    if len(addr) == 2:
        # Lets hope it is an address followed by a port.
        return "[%s]:%d" % (inet_ntop(AF_INET6, addr[0], addr[1]))
    # Address only.
    return inet_ntop(AF_INET6, addr)

def ipv6_from_str(str):
    return inet_pton(AF_INET6, str)

if __name__ == "__main__":
    addr = inet_pton(AF_INET6, "fe80:ffff:ffff:ffff:ffff:ffff:ffff:ffff")
    print("ipv6_prefix(%s, 16): %s" % (ipv6_to_str(addr), ipv6_to_str(ipv6_prefix(addr, 16))))
    print("ipv6_prefix(%s, 4): %s" % (ipv6_to_str(addr), ipv6_to_str(ipv6_prefix(addr, 4))))
    print("ipv6_prefix(%s, 8): %s" % (ipv6_to_str(addr), ipv6_to_str(ipv6_prefix(addr, 8))))
    print("ipv6_prefix(%s, 64): %s" % (ipv6_to_str(addr), ipv6_to_str(ipv6_prefix(addr, 64))))

    p1 = ipv6_from_str("2001:1234::")
    p2 = ipv6_from_str("2001:1270::")
    print("ipv6_prefix_eq(%s, %s, 0): %d" % (ipv6_to_str(p1), ipv6_to_str(p2), ipv6_prefix_eq(p1, p2, 0)))
    print("ipv6_prefix_eq(%s, %s, 24): %d" % (ipv6_to_str(p1), ipv6_to_str(p2), ipv6_prefix_eq(p1, p2, 24)))
    print("ipv6_prefix_eq(%s, %s, 25): %d" % (ipv6_to_str(p1), ipv6_to_str(p2), ipv6_prefix_eq(p1, p2, 25)))
    print("ipv6_prefix_eq(%s, %s, 26): %d" % (ipv6_to_str(p1), ipv6_to_str(p2), ipv6_prefix_eq(p1, p2, 26)))
    print("ipv6_prefix_eq(%s, %s, 128): %d" % (ipv6_to_str(p1), ipv6_to_str(p2), ipv6_prefix_eq(p1, p2, 128)))

