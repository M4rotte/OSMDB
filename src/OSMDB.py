# pylint: disable=bad-whitespace,bad-continuation,line-too-long,multiple-statements,trailing-whitespace,trailing-newlines,invalid-name,trailing-whitespace
# -*- coding: UTF-8 -*-
"""OSMDB"""
import sys
import ipaddress
import subprocess
import Host
from multiprocessing import Process, Queue

def getDefaultRoute(): return str(subprocess.check_output(['ip','route'], universal_newlines=True).splitlines()[1]).split(' ')[0]
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n): yield l[i:i + n]

class OSMDB:
    
    def __init__(self, configuration, db):
        
        self.db = db
        self.configuration = configuration
        
    def pingHosts(self, network = '127.0.0.0/8'):
        """Ping all hosts in a given network and update the database. It returns the list of hosts.
           If False is specified as the network argument it will use the `ip route` external command
           to get the default route and will use this route."""
        hosts = []
        if not network: network = getDefaultRoute()
        try: net = ipaddress.IPv4Network(network)
        except ValueError as e:
            print('Invalid network specification: '+str(e))
            return hosts
        addresses = list(net.hosts())
        remaining = len(addresses)
        queue = Queue()
        try:
            for chunk in chunks(list(net.hosts()), self.configuration['chunk_size']):
                remaining -= len(chunk)
                first = chunk[0]
                last = chunk[-1:][0]
                print('Processing {} hosts… {} → {} (remains:{})'.format(str(len(chunk)), first, last, str(remaining)))
                for address in chunk:
                    host = Host.Host()
                    Process(target=host.process, args=(address, queue)).start()

                for host in chunk:
                    hosts.append(queue.get())
                    
        except KeyboardInterrupt:
            print('Host update cancelled!',file=sys.stderr)
            return []
        
        return hosts

    def updateHosts(self, ping_delays): self.db.updateHosts(ping_delays)
    def listHosts(self):
        for host in self.db.listHosts():
            print(host)

if __name__ == '__main__': sys.exit(100)
