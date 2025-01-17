"""This file contains a simple crash test for RIPng topology"""

from ipmininet.iptopo import IPTopo
from ipmininet.router.config.ripng import RIPng
from ipmininet.router.config import RouterConfig


class RIPngNetwork(IPTopo):

    def build(self, *args, **kwargs):
        """
        +-----+     +-----+  2  +-----+     +-----+     +-----+
        | h1  +-----+ r1  +-----+ r2  +-----+ r3  +-----+ h3  |
        +-----+     +--+--+     +--+--+     +-----+     +-----+
                       |           |       /
                       |           |      / 
                       |           |     / 5
                       |           |    /
                       |           |   /
        +-----+     +--+--+     +--+--+     +-----+
        | h4  +-----+ r4  +-----+ r5  +-----+ h5  |
        +-----+     +-----+     +-----+     +-----+
        """
        r1 = self.addRouter_v6('r1')
        r2 = self.addRouter_v6('r2')
        r3 = self.addRouter_v6('r3')
        r4 = self.addRouter_v6('r4')
        r5 = self.addRouter_v6('r5')

        h1 = self.addHost('h1')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')

        self.addLink(h1, r1)
        self.addLink(h3, r3)
        self.addLink(h4, r4)
        self.addLink(h5, r5)

        lr1r2 = self.addLink(r1, r2, igp_metric=2)
        lr1r2[r1].addParams(ip=("2042:12::1/64"))
        lr1r2[r2].addParams(ip=("2042:12::2/64"))
        lr1r4 = self.addLink(r1, r4)
        lr1r4[r1].addParams(ip="2042:14::1/64")
        lr1r4[r4].addParams(ip="2042:14::4/64")
        lr2r3 = self.addLink(r2, r3)
        lr2r3[r2].addParams(ip="2042:23::2/64")
        lr2r3[r3].addParams(ip="2042:23::3/64")
        lr2r5 = self.addLink(r2, r5)
        lr2r5[r2].addParams(ip="2042:25::2/64")
        lr2r5[r5].addParams(ip="2042:25::5/64")
        lr3r5 = self.addLink(r3, r5, igp_metric=5)
        lr3r5[r3].addParams(ip="2042:35::3/64")
        lr3r5[r5].addParams(ip="2042:35::5/64")
        lr4r5 = self.addLink(r4, r5)
        lr4r5[r4].addParams(ip="2042:45::4/64")
        lr4r5[r5].addParams(ip="2042:45::5/64")

        self.addSubnet(nodes=[r1, h1], subnets=["2042:11::/64"])
        self.addSubnet(nodes=[r3, h3], subnets=["2042:33::/64"])
        self.addSubnet(nodes=[r4, h4], subnets=["2042:44::/64"])
        self.addSubnet(nodes=[r5, h5], subnets=["2042:55::/64"])

        r1.addDaemon(RIPng, timeout_timer=1, garbage_timer=2)
        r2.addDaemon(RIPng, timeout_timer=1, garbage_timer=2)
        r3.addDaemon(RIPng, timeout_timer=1, garbage_timer=2)
        r4.addDaemon(RIPng, timeout_timer=1, garbage_timer=2)
        r5.addDaemon(RIPng, timeout_timer=1, garbage_timer=2)

        super(RIPngNetwork, self).build(*args, **kwargs)

    def addRouter_v6(self, name):
        return self.addRouter(name, use_v4=False, use_v6=True, config=RouterConfig)

