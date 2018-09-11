import ifaddr
import socket
import os
from hetznercloud.servers import HetznerCloudServer

#
# Validators
#
class Ipv4Validator:
    def __init__(self, parameter):
        self.parameter = parameter

    def __call__(self):
        try:
            socket.inet_aton( self.parameter.get() )
        except socket.error:
            raise EnvironmentError(0, "Parameter "+self.parameter.name+" is not a valid ipv4 address")

class StringLengthValidator:
    def __init__(self, parameter, length):
        self.parameter = parameter
        self.length = length

    def __call__(self):
        if len( self.parameter.get() ) == self.length:
            return

        raise EnvironmentError(0, "Parameter "+self.parameter.name+" does not have the length of a hetzner cloud token("+str(self.length)+" characters)")
            


#
# The HostFinder searches for the hetzner cloud api server which manages the
# machine this script is running on
#
# Implementation:
#   An api server is matched if the ipv4 address listed in the api is present
#   on this machine
#  
# Possible alternatives:
# Match hostname to servername
#
#
class HostFinder:
    def find(self, client) -> HetznerCloudServer:
        pass

class IpHostFinder(HostFinder):
    def __init__(self, ipApi = ifaddr):
        self.ipApi = ipApi

    def find(self, client) -> HetznerCloudServer:
        my_ips = []
        adapters = self.ipApi.get_adapters()
        for adapter in adapters:
            for ip in adapter.ips:
                my_ips.append(ip.ip)
        servers = client.servers().get_all()
        for server in servers:
            if server.public_net_ipv4 in  my_ips:
                return server
        raise EnvironmentError('Host not found in hcloud api.')

class HostnameHostFinder(HostFinder):
    def __init__(self, hostname):
        self.hostname = hostname

    def find(self, client) -> HetznerCloudServer:
        success = False
        while not success:
            servers = list(client.servers().get_all(name=self.hostname))
            success = True
        if len(servers) < 1:
            raise EnvironmentError('Host '+self.hostname+' not found in hcloud api.')
        return servers[0]

class TestHostFinder(HostFinder):
    def find(self, client) -> HetznerCloudServer:
        name = os.environ.get('TESTHOST')
        servers = client.servers().get_all(name=name)
        if len(servers) < 1:
            raise EnvironmentError('Host '+name+' not found in hcloud api.')
        return servers[0]

def makeHostFinder(type) -> HostFinder:
    if type == 'public-ip':
        return IpHostFinder()
    if type == 'hostname':
        hostname = socket.gethostname()
        return HostnameHostFinder(hostname)
    if type == 'test':
        return TestHostFinder()
    raise KeyError('Unkown host finder type')

