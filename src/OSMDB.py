# pylint: disable=bad-whitespace,bad-continuation,line-too-long,multiple-statements,trailing-whitespace,trailing-newlines,invalid-name,trailing-whitespace
# -*- coding: UTF-8 -*-
"""OSMDB"""
import sys
import ipaddress
import subprocess
import Host, Logger
from multiprocessing import Process, Queue
from datetime import timedelta
from time import time

def getDefaultRoute(): 
    """Call the external command `ip route`. This only works with Linux. The default route is used if no network is given in the command line (--network)."""
    return str(subprocess.check_output(['ip','route'], universal_newlines=True).splitlines()[1]).split(' ')[0]

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n): yield l[i:i + n]

class OSMDB:
    """The Overly Simple Management Database main object."""
    def __init__(self, configuration, db, logger = Logger.Logger()):
        
        self.db = db
        self.configuration = configuration
        self.logger = logger
        
    def __repr__(self): return 'OSMDB'
        
    def pingHosts(self, network = '127.0.0.0/8'):
        """Ping all hosts in a given network and update the database. It returns the list
           of hosts, each host being a triplet (hostname, fqdn, ping_delay).
           If network is False the `ip route` external command will be called
           to get the default route and use it."""
        hosts = []
        if not network: network = getDefaultRoute()
        try: net = ipaddress.IPv4Network(network)
        except ValueError as e:
            print('Invalid network specification: '+str(e), file=sys.stderr)
            return hosts
        addresses = list(net.hosts())
        remaining = len(addresses)
        queue = Queue(remaining)
        self.logger.log('Processing {} addresses in batches of {}.'.format(remaining, str(self.configuration['chunk_size'])), 0)
        batch_index = 1
        start = time()
        try:
            for chunk in chunks(list(net.hosts()), self.configuration['chunk_size']):
                remaining -= len(chunk)
                first = chunk[0]
                last = chunk[-1:][0]
                self.logger.log('Batch #{:03d} ({}) {} → {}, ({} left)'.format(batch_index, str(len(chunk)), first, last, str(remaining)), 0)
                for address in chunk:
                    host = Host.Host()
                    Process(target=host.process, args=(address, queue)).start()

                for host in chunk:
                    hosts.append(queue.get())
                    
                batch_index += 1
        
            end = time()
            elapsed = str(timedelta(seconds=(end - start)))
            rate = len(addresses) / (end - start)
            self.logger.log('{} addresses scanned in {} ({:.2f} a/s)'.format(len(addresses), elapsed, rate), 0)

        except KeyboardInterrupt:
            self.logger.log('Host update cancelled!', 5)
            return []
        
        return hosts

    def updateHosts(self, ping_delays): self.db.updateHosts(ping_delays)
    def listHosts(self):
        for host in self.db.listHosts():
            print(host)

if __name__ == '__main__': sys.exit(100)
