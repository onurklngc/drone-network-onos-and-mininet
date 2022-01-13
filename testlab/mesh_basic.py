#!/usr/bin/python

'This example shows how to create wireless link between two APs'

from mininet.log import setLogLevel, info
from mininet.node import RemoteController, Controller
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd, mesh
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference

IS_REMOTE_CONTROLLER = True
AP_TX_POWER = 24
AP_MESH_TX_POWER = 15
STA_TX_POWER = 24
MESH_CHANNEL = 157


def topology():
    "Create a network."
    net = Mininet_wifi(controller=RemoteController if IS_REMOTE_CONTROLLER else Controller,
                       link=wmediumd, wmediumd_mode=interference, xterms=True, noise_th=-75)

    info("*** Creating nodes\n")

    sta1 = net.addStation('sta1', mac='00:00:00:00:00:11', position='125,1,0')
    sta2 = net.addStation('sta2', mac='00:00:00:00:00:12', position='151,51,0')
    ap1 = net.addAccessPoint('ap1', wlans=2, ssid='ssid1', position='300,10,0', channel=1, protocols='OpenFlow13')
    sta3 = net.addStation('sta3', mac='00:00:00:00:00:13', position='675,11,0')
    sta4 = net.addStation('sta4', mac='00:00:00:00:00:14', position='651,52,0')
    ap2 = net.addAccessPoint('ap2', wlans=2, ssid='ssid2', position='500,10,0', channel=2, protocols='OpenFlow13')
    sta5 = net.addStation('sta5', mac='00:00:00:00:00:15', position='851,52,0')
    ap3 = net.addAccessPoint('ap3', wlans=2, ssid='ssid3', position='700,10,0', channel=3, protocols='OpenFlow13')
    h1 = net.addHost('h%d' % 1, mac='00:00:00:00:00:' + hex(1).split('x')[-1].zfill(2))
    h2 = net.addHost('h%d' % 2, mac='00:00:00:00:00:' + hex(2).split('x')[-1].zfill(2))
    if IS_REMOTE_CONTROLLER:
        c0 = net.addController(name='c0',
                               controller=RemoteController,
                               ip='127.0.0.1',
                               protocol='tcp',
                               port=6653, protocols="OpenFlow13")
    else:
        c0 = net.addController(name='c0', port=6654)
    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="losNlosMixture", exp=2)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info("*** Associating Stations\n")
    # net.addLink(ap1, sta1, ht_cap='HT40+')
    # net.addLink(ap2, sta2, ht_cap='HT40+')
    net.addLink(h1, ap1, bw=100, delay='0ms')
    net.addLink(h2, ap2, bw=100, delay='0ms')
    # net.addLink(ap1, ap2, bw=100, delay='0ms')
    net.addLink(ap1, intf='ap1-wlan2', cls=mesh, ssid='mesh-ssid', mode="a", channel=MESH_CHANNEL,
                txpower=AP_MESH_TX_POWER)
    net.addLink(ap2, intf='ap2-wlan2', cls=mesh, ssid='mesh-ssid', mode="a", channel=MESH_CHANNEL,
                txpower=AP_MESH_TX_POWER)
    net.addLink(ap3, intf='ap3-wlan2', cls=mesh, ssid='mesh-ssid', mode="a", channel=MESH_CHANNEL,
                txpower=AP_MESH_TX_POWER)

    info("*** Starting network\n")
    net.plotGraph(max_x=1000, max_y=500, min_x=-70, min_y=-70)
    net.build()
    c0.start()
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])
    net.plotGraph(max_x=3000, max_y=1000)

    print("AP1 radius %f" % ap1.get_max_radius())
    ap1.setTxPower(AP_TX_POWER, intf='ap1-wlan1')
    print("AP1 radius %f" % ap1.get_max_radius())
    print("AP2 radius %f" % ap1.get_max_radius())
    ap2.setTxPower(AP_TX_POWER, intf='ap2-wlan1')
    ap3.setTxPower(AP_TX_POWER, intf='ap3-wlan1')

    print("Sta1 radius %f" % sta1.get_max_radius())
    sta1.setTxPower(STA_TX_POWER)
    print("Sta1 radius %f" % sta1.get_max_radius())
    sta2.setTxPower(STA_TX_POWER)
    sta3.setTxPower(STA_TX_POWER)
    sta4.setTxPower(STA_TX_POWER)
    sta5.setTxPower(STA_TX_POWER)

    sta1.setRange(120)
    # ap1.setTxPower(20)
    # print("AP1 radius %f" % ap1.get_max_radius())
    # ap1.setTxPower(25, intf="ap1-mp2")
    # print("AP1 radius %f" % ap1.get_max_radius())
    # ap1.setTxPower(25, intf="ap1-wlan1")
    # print("AP1 radius %f" % ap1.get_max_radius())
    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('debug')
    topology()