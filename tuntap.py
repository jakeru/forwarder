import fcntl
import struct
import os

TUNSETIFF = 0x400454ca
TUNSETOWNER = TUNSETIFF + 2
IFF_TUN = 0x0001
IFF_TAP = 0x0002
IFF_NO_PI = 0x1000

def tun_open(dev, mode="tun"):
    """ Opens an existing tuntap device named dev. The mode should be set to
        tun or tap and must match the already created device.
        To create a tap device, write:
        sudo ip tuntap add dev tap0 mode tap
        To bring it up, write:
        sudo ip link set tun0 up
        """
    # Open TUN device file.
    tun = os.open('/dev/net/tun', os.O_RDWR)
    flags = IFF_NO_PI
    if mode=="tap":
        flags = flags | IFF_TAP
    else:
        flags = flags | IFF_TUN
    ifr = struct.pack('16sH', dev, IFF_TUN | IFF_NO_PI)
    fcntl.ioctl(tun, TUNSETIFF, ifr)
    return tun