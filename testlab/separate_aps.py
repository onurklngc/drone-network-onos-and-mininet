#!/usr/bin/python

from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd
from mn_wifi.net import Mininet_wifi
from mn_wifi.node import OVSKernelAP
from mn_wifi.wmediumdConnector import interference


def myNetwork():
    net = Mininet_wifi(topo=None,
                       build=False,
                       link=wmediumd,
                       wmediumd_mode=interference,
                       ipBase='10.0.0.0/8')

    info('*** Adding controller\n')
    info('*** Add switches/APs\n')
    ap1 = net.addAccessPoint('ap1', cls=OVSKernelAP, ssid='ap1-ssid',
                             channel='36', mode='a', position='337.0,424.0,0', ht_cap='HT40+')
    ap2 = net.addAccessPoint('ap2', cls=OVSKernelAP, ssid='ap2-ssid',
                             channel='1', mode='g', position='1368.0,391.0,0')
    ap3 = net.addAccessPoint('ap3', cls=OVSKernelAP, ssid='ap3-ssid',
                             channel='36', mode='a', ht_cap='HT40+', position='2368.0,391.0,0')

    info('*** Add hosts/stations\n')
    sta1 = net.addStation('sta1', ip='10.0.0.1',
                          position='192.0,384.0,0')
    sta2 = net.addStation('sta2', ip='10.0.0.2',
                          position='237.0,443.0,0')
    sta3 = net.addStation('sta3', ip='10.0.0.3',
                          position='1493.0,150.0,0')
    sta4 = net.addStation('sta4', ip='10.0.0.4',
                          position='1374.0,656.0,0')
    sta5 = net.addStation('sta5', ip='10.0.0.5',
                          position='2393.0,350.0,0')
    sta6 = net.addStation('sta6', ip='10.0.0.6',
                          position='2374.0,426.0,0')
    h1 = net.addHost('h%d' % 1, mac='00:00:00:55:00:' + hex(1).split('x')[-1].zfill(2))
    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=3)

    # Defining 3 mediums for packet ordering
    net.setInitialMediums((("sta1-wlan0", sta2, ap1),  # Medium #1
                           (sta3, sta4, "ap2-wlan1"),  # Medium #2
                           (sta5,)  # Medium #3
                           ))

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()
    net.addLink(h1, ap1, bw=100, delay='0ms')
    net.plotGraph(max_x=1000, max_y=1000)

    info('*** Starting network\n')
    net.build()
    info('*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info('*** Starting switches/APs\n')
    net.get('ap1').start([])
    net.get('ap2').start([])
    net.get('ap3').start([])

    info('*** Post configure nodes\n')

    # Adding ap3's first interface to medium #3
    ap3.setMediumId(3, intf=None)
    # Adding sta6-wlan0 interface to medium #3
    sta6.getNameToWintf("sta6-wlan0").setMediumId(3)
    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('debug')
    myNetwork()
