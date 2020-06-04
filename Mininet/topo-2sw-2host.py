"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        FirstHost = self.addHost( 'h1' ) 
        SecHost = self.addHost( 'h2' )
        ThirdHost = self.addHost( 'h3' )
        FourthHost = self.addHost( 'h4' )
        FivethHost = self.addHost( 'h5' )
        FirstSwitch = self.addSwitch( 's1' )

        # Add links
        self.addLink( FirstHost, FirstSwitch )
        self.addLink( SecHost, FirstSwitch )
        self.addLink( ThirdHost, FirstSwitch )
        self.addLink( FourthHost, FirstSwitch )
        self.addLink( FivethHost, FirstSwitch )

topos = { 'mytopo': ( lambda: MyTopo() ) }
