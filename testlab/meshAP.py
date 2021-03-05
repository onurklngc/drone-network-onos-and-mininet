#!/usr/bin/python

'This example shows how to create wireless link between two APs'

from mininet.log import setLogLevel, info
from mininet.node import RemoteController, Controller
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd, mesh
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference

IS_REMOTE_CONTROLLER = False


def topology():
    "Create a network."
    net = Mininet_wifi(controller=RemoteController if IS_REMOTE_CONTROLLER else Controller,
                       link=wmediumd, wmediumd_mode=interference, mode="g")

    info("*** Creating nodes\n")
    sta1 = net.addStation('sta1', mac='00:00:00:00:00:11', position='1,100,0')
    sta2 = net.addStation('sta2', mac='00:00:00:00:00:12', position='610,380,0')
    sta3 = net.addStation('sta3', mac='00:00:00:00:00:13', position='950,100,0')
    sta4 = net.addStation('sta4', mac='00:00:00:00:00:14', position='200,100,0')
    ap1 = net.addAccessPoint('ap1', wlans=3, ssid='ssid1', channel=9, position='310,100,0')
    ap2 = net.addAccessPoint('ap2', wlans=3, ssid='ssid2', channel=10, position='600,100,0')
    ap3 = net.addAccessPoint('ap3', wlans=3, ssid='ssid3', channel=11, position='900,100,0')

    h1 = net.addHost('h%d' % 1, mac='00:00:00:00:00:' + hex(1).split('x')[-1].zfill(2))
    h2 = net.addHost('h%d' % 2, mac='00:00:00:00:00:' + hex(2).split('x')[-1].zfill(2))
    h3 = net.addHost('h%d' % 3, mac='00:00:00:00:00:' + hex(3).split('x')[-1].zfill(2))

    if IS_REMOTE_CONTROLLER:
        c0 = net.addController(name='c0',
                               controller=RemoteController,
                               ip='127.0.0.1',
                               protocol='tcp',
                               port=6653)
    else:
        c0 = net.addController(name='c0', port=6654)
    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=3)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info("*** Associating Stations\n")
    net.addLink(sta1, ap1)
    net.addLink(sta4, ap1)
    net.addLink(h1, ap1, bw=100, delay='0ms')
    net.addLink(h3, ap3, bw=100, delay='0ms')
    net.addLink(h2, ap2, bw=100, delay='0ms')
    net.addLink(sta2, ap2)
    net.addLink(sta3, ap3)
    net.addLink(ap1, intf='ap1-wlan2', cls=mesh, ssid='mesh-ssid12', channel=4, ht_cap='HT40+')
    net.addLink(ap2, intf='ap2-wlan2', cls=mesh, ssid='mesh-ssid12', channel=4, ht_cap='HT40+')
    net.addLink(ap2, intf='ap2-wlan3', cls=mesh, ssid='mesh-ssid23', channel=4, ht_cap='HT40+')
    net.addLink(ap3, intf='ap3-wlan2', cls=mesh, ssid='mesh-ssid23', channel=4, ht_cap='HT40+')
    # net.addLink(ap2, intf='ap1-wlan3', cls=mesh, ssid='mesh-ssid13', channel=4, ht_cap='HT40+')
    # net.addLink(ap3, intf='ap3-wlan3', cls=mesh, ssid='mesh-ssid13', channel=4, ht_cap='HT40+')
    info("*** Starting network\n")
    net.plotGraph(max_x=1000, max_y=400, min_x=0, min_y=-70)
    net.build()
    c0.start()
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])

    # CLI(net)
    # net.getNodeByName("ap3").intfs.get(2).link.ssid = "pi"
    # CLI(net)
    # net.getNodeByName("ap2").intfs.get(3).link.ssid = 'mesh-ssid2'

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('debug')
    topology()
