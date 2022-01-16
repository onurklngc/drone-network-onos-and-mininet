#!/usr/bin/python

'This example shows how to create wireless link between two APs'

from mininet.log import setLogLevel, info
from mininet.node import RemoteController, Controller
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference

IS_REMOTE_CONTROLLER = True
AP_TX_POWER = 27
AP_GAIN = 3
STA_TX_POWER = 27
STA_GAIN = 3


def topology():
    "Create a network."
    net = Mininet_wifi(controller=RemoteController if IS_REMOTE_CONTROLLER else Controller,
                       link=wmediumd, wmediumd_mode=interference, xterms=True, noise_th=-75)

    info("*** Creating nodes\n")

    sta1 = net.addStation('sta1', mac='00:00:00:00:00:01', position='100,50,0')
    sta2 = net.addStation('sta2', mac='00:00:00:00:00:02', position='200,0,0')
    ap1 = net.addAccessPoint('ap1', ssid='ssid1', position='0,0,100', channel=5, ht_capab='HT40+',
                             protocols='OpenFlow13')
    h1 = net.addHost('h%d' % 1, mac='01:00:00:00:00:' + hex(1).split('x')[-1].zfill(2))

    if IS_REMOTE_CONTROLLER:
        c0 = net.addController(name='c0',
                               controller=RemoteController,
                               ip='127.0.0.1',
                               protocol='tcp',
                               port=6653)
    else:
        c0 = net.addController(name='c0', port=6654)
    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="losNlosMixture", exp=2, uav_default_height=100)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info("*** Associating Stations\n")

    net.addLink(h1, ap1, bw=100, delay='0ms')
    info("*** Starting network\n")
    net.plotGraph(max_x=1000, max_y=500, min_x=-70, min_y=-70)
    net.build()
    c0.start()
    ap1.start([c0])

    ap1.setTxPower(AP_TX_POWER, intf='ap1-wlan1')
    ap1.setAntennaGain(AP_GAIN, intf='ap1-wlan1')
    print("AP1 radius %f" % ap1.get_max_radius())
    sta1.setTxPower(STA_TX_POWER)
    sta2.setTxPower(STA_TX_POWER)
    sta1.setAntennaGain(STA_GAIN)
    sta2.setAntennaGain(STA_GAIN)
    print("sta1 radius %f" % sta1.get_max_radius())

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('debug')
    topology()
