#!/usr/bin/python

from mininet.log import setLogLevel, info
from mininet.node import RemoteController
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference, snr


def myNetwork():
    net = Mininet_wifi(controller=RemoteController, link=wmediumd,
                       wmediumd_mode=snr)

    info('*** Adding controller\n')
    c0 = net.addController(name='c0',
                           controller=RemoteController,
                           ip='127.0.0.1',
                           protocol='tcp',
                           port=6653)

    info('*** Add switches/APs\n')
    ap1 = net.addAccessPoint('ap1', ssid='ap1-ssid',
                             channel='1', mode='g', position='306,252,0')
    ap2 = net.addAccessPoint('ap2', ssid='ap2-ssid',
                             channel='1', mode='g', position='380,252,0')
    # ap3 = net.addAccessPoint('ap3', wlans=2, ssid="ap3-ssid", mode="g",
    #                          channel="1", position='50,30,0')
    info('*** Add hosts/stations\n')
    sta1 = net.addStation('sta1', ip='10.0.0.1/24',
                          position='233.0,437.0,0')
    sta2 = net.addStation('sta2', ip='10.0.0.2/24',
                          position='400.0,270.0,0')
    sta3 = net.addStation('sta3', ip='10.0.0.3/24',
                          position='247.0,50.0,0')

    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=3)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info('*** Add links\n')
    net.addLink(ap1, ap2)
    net.addLink(sta1, ap1)
    net.addLink(sta2, ap2)
    net.addLink(sta3, ap1)

    net.plotGraph(max_x=1500, max_y=1000)

    info('*** Starting network\n')
    net.build()
    info('*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info('*** Starting switches/APs\n')
    ap1.start([c0])
    ap2.start([c0])

    info('*** Post configure nodes\n')
    sta1.setPosition('111.0,123.0,0')
    # ap1.setAntennaGain(100)
    # ap1.setRange(700)
    # ap2.setRange(700)
    # ap1.setPosition('111.0,123.0,0')
    # sta1.setAssociation(ap1, intf='sta1-wlan0')
    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    myNetwork()
