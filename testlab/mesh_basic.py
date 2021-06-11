#!/usr/bin/python

'This example shows how to create wireless link between two APs'

from mininet.log import setLogLevel, info
from mininet.node import RemoteController, Controller
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd, mesh
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference

IS_REMOTE_CONTROLLER = True


def topology():
    "Create a network."
    net = Mininet_wifi(controller=RemoteController if IS_REMOTE_CONTROLLER else Controller,
                       link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")

    sta1 = net.addStation('sta1', mac='00:00:00:00:00:11', position='1,1,0')
    sta2 = net.addStation('sta2', mac='00:00:00:00:00:12', position='31,11,0')
    ap1 = net.addAccessPoint('ap1', wlans=2, ssid='ssid1', position='10,10,0')
    ap2 = net.addAccessPoint('ap2', wlans=2, ssid='ssid2', position='30,10,0')

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
    net.addLink(sta2, ap2)

    net.addLink(ap1, intf='ap1-wlan2', cls=mesh, ssid='mesh-ssid', channel=5)
    net.addLink(ap2, intf='ap2-wlan2', cls=mesh, ssid='mesh-ssid', channel=5)
    info("*** Starting network\n")
    net.plotGraph(max_x=1000, max_y=500, min_x=-70, min_y=-70)
    net.build()
    c0.start()
    ap1.start([c0])
    ap2.start([c0])

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('debug')
    topology()
