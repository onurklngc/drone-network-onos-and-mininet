import re
import os
from time import sleep

from mininet.net import Mininet
from mininet.link import TCIntf
from mininet.log import setLogLevel, info
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.node import Node, Controller, OVSKernelSwitch, RemoteController

CONTROLLER_IP = "192.168.56.3"
TARGET_BW = 500
INITIAL_BW = 1000

class BasicTopo(Topo):
    "Simple topo with 2 hosts"
    def build(self):
        switch1 = self.addSwitch('s1')
        switch2 = self.addSwitch('s2')
        switch3 = self.addSwitch('s3')
        self.addLink(switch1, switch2, bw=1000)
        self.addLink(switch1, switch3, bw=1000)
        self.addLink(switch2, switch3, bw=INITIAL_BW)


        host1 = self.addHost('h1')
        self.addLink(host1, switch1, bw = INITIAL_BW)

        host2 = self.addHost('h2')
        self.addLink(host2, switch2, bw = INITIAL_BW)
        host3 = self.addHost('h3')
        self.addLink(host3, switch2, bw = INITIAL_BW)
        host4 = self.addHost('h4')
        self.addLink(host4, switch3, bw = INITIAL_BW)

def measureChange(h1, h2, smooth_change, output_file_name, target_bw = TARGET_BW):
    info( "Starting iperf Measurement\n" )

    # stop old iperf server
    os.system('pkill -f \'iperf -s\'')

    h1.cmd('iperf -s -i 0.5 -y C > ' + output_file_name + ' &')
    h2.cmd('iperf -c ' + str(h1.IP()) + ' -t 10 -i 1 > /dev/null &')

    # wait 5 seconds before changing
    sleep(5)

    intf = h2.intf()
    info( "Setting BW Limit for Interface " + str(intf) + " to " + str(target_bw) + "\n" )
    intf.config(bw = target_bw)

    # wait a few seconds to finish
    sleep(10)

def startNetwork():
    """Example of changing the TCLinklimits"""
    myTopo = BasicTopo()

    net = Mininet( topo=myTopo, link=TCLink, controller=RemoteController, switch=OVSKernelSwitch )
    c1 = net.addController('c1', controller=RemoteController, ip=CONTROLLER_IP)
    net.addNAT().configDefault()
    net.start()
    print(net.get("s2").connectionsTo(net.get("s1")))
    print(net.get("s2").connectionsTo(net.get("s1"))[0])
    CLI(net)
    # h1 = net.get('h1')
    # h2 = net.get('h2')
    # intf = h2.intf()
    #
    # traces = []
    #
    # # reset bw to initial value
    # intf.config(bw = INITIAL_BW)
    net.stop()



if __name__ == '__main__':
     setLogLevel( 'info' )
     startNetwork()