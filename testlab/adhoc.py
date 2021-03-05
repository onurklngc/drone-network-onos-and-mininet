#!/usr/bin/python

"""
This example shows on how to enable the adhoc mode
Alternatively, you can use the manet routing protocol of your choice
"""

import sys

from mininet.log import setLogLevel, info
from mininet.node import Controller
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd, mesh
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference


def topology(args):
    "Create a network."
    net = Mininet_wifi(controller=Controller, link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    kwargs = dict()
    if '-a' in args:
        kwargs['range'] = 100

    sta1 = net.addStation('sta1', ip6='fe80::1', position='10,10,0', **kwargs)
    sta2 = net.addStation('sta2', ip6='fe80::2', position='50,10,0', **kwargs)
    sta3 = net.addStation('sta3', ip6='fe80::3', position='90,10,0', **kwargs)
    sta4 = net.addStation('sta4', ip6='fe80::4', position='-40,10,0', **kwargs)
    ap1 = net.addAccessPoint('ap1', ssid="ap1-ssid", mode="n", channel="1", position='0,0,0')
    ap2 = net.addAccessPoint('ap2', ssid="ap2-ssid", mode="n", channel="1", position='60,10,0')
    ap3 = net.addAccessPoint('ap3', ssid="ap3-ssid", mode="n", channel="1", position='95,20,0')

    l1a = net.addAccessPoint('ap1004', wlans=2, position='1000,0,0')
    l1b = net.addAccessPoint('ap1005', wlans=2, position='1060,10,0')
    l2a = net.addAccessPoint('ap1006', wlans=2, position='1500,0,0')
    l2b = net.addAccessPoint('ap1007', wlans=2, position='1560,10,0')
    c0 = net.addController(name='c0'
                           )

    net.setPropagationModel(model="logDistance", exp=4)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info("*** Creating links\n")

    net.addLink(sta1, ap1)
    net.addLink(sta4, ap1)
    net.addLink(sta2, ap2)
    net.addLink(sta3, ap3)

    net.addLink(ap1, l1a, delay='0ms', bw=100)
    net.addLink(ap2, l1b, delay='0ms', bw=100)
    net.addLink(ap2, l2a, delay='0ms', bw=100)
    net.addLink(ap3, l2b, delay='0ms', bw=100)
    net.addLink(l1a, intf='ap1004-wlan2', cls=mesh, ssid='l1-mesh', channel=5, ht_cap='HT40+', mode="n")
    net.addLink(l1b, intf='ap1005-wlan2', cls=mesh, ssid='l1-mesh', channel=5, ht_cap='HT40+', mode="n")
    net.addLink(l2a, intf='ap1006-wlan2', cls=mesh, ssid='l2-mesh', channel=6, ht_cap='HT40+', mode="n")
    net.addLink(l2b, intf='ap1007-wlan2', cls=mesh, ssid='l2-mesh', channel=6, ht_cap='HT40+', mode="n")
    # net.addLink(ap1, ap3, cls=wmediumd)

    net.plotGraph(max_x=150, max_y=100, min_x=-70, min_y=-70)

    info("*** Starting network\n")
    net.build()
    c0.start()
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])
    l1a.start([c0])
    l1b.start([c0])
    l2a.start([c0])
    l2b.start([c0])

    info("\n*** Addressing...\n")
    if 'proto' not in kwargs:
        sta1.setIP6('2001::1/64', intf="sta1-wlan0")
        sta2.setIP6('2001::2/64', intf="sta2-wlan0")
        sta3.setIP6('2001::3/64', intf="sta3-wlan0")
        sta4.setIP6('2001::4/64', intf="sta4-wlan0")

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology(sys.argv)
