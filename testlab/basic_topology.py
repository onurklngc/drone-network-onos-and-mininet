from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.topo import Topo

mn_ip = '192.168.2.50'

class MyTopo(Topo):
    "Simple topology example."

    def build(self):
        "Create custom topo."
        # Add hosts and switches
        leftHost = self.addHost('h1')
        rightHost = self.addHost('h2')
        leftSwitch = self.addSwitch('s1')
        rightSwitch = self.addSwitch('s2')
        # Add links
        self.addLink(leftHost, leftSwitch)
        self.addLink(leftSwitch, rightSwitch)
        self.addLink(rightSwitch, rightHost)


mininet_network = Mininet(topo=MyTopo(), controller=RemoteController('main_controller', ip=mn_ip, port=6653),
                          switch=OVSKernelSwitch)
mininet_network.start()
CLI(mininet_network)