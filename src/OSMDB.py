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
import Host, SSHClient, Execution

def getDefaultRoute(): 
    """Call the external command `ip route`. This only works with Linux. The default route is used if no network is given in the command line (--network)."""
    return str(subprocess.check_output(['ip','route'], universal_newlines=True).splitlines()[1]).split(' ')[0]

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n): yield l[i:i + n]

def lprint(l):
    if type(l) is not list: l = list(l)
    for i in l: print(i)

class OSMDB:
    """The Overly Simple Management Database main object."""
    def __init__(self, configuration, db, logger = Logger.Logger()):
        
        self.db = db
        self.configuration = configuration
        self.logger = logger
        self.configuration['ping_chunk_size'] = self.configuration.get('ping_chunk_size', 32)
        
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
        self.logger.log('Processing {} addresses in batches of {}.'.format(remaining, str(self.configuration['ping_chunk_size'])), 0)
        batch_index = 1
        start = time()
        try:
            for chunk in chunks(list(net.hosts()), self.configuration['ping_chunk_size']):
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
            self.logger.log('Host update cancelled by keyboard interrupt!', 5)
        
        return hosts

    def updateHosts(self, ping_delays, network_name = None): self.db.updateHosts(ping_delays, network_name)
    def execOnHosts(self,command='a', hosts = []):
        hosts = list(map(Host.Host, hosts))
        executions = list(map(Execution.Execution, self.ssh.execute(command, hosts)))
        lprint(executions)
        self.db.addExecutions(executions)
    def listHosts(self, hosts):
        lprint(hosts)
    def listHostUpdates(self):
        lprint(self.db.listHostUpdates())
    def deploy(self, key, hosts):
        """Add the public key of OSMDB in the authorized_keys file of the given hosts."""
        self.ssh.deploy(key, list(map(Host.Host,hosts)))
    def selectHosts(self, query = ''):
        return self.db.hosts(query=query)
    def listExecutions(self):
        for execution in self.db.listExecutions():
            execution_l = list(execution)
            execution_l[1] = Host.Host((execution[1],execution[1],None))
            execution_l[4] = execution[4].split('\n')
            execution_l[5] = execution[5].split('\n')
            print(Execution.Execution(execution_l))
    def purgeHosts(self, addresses = '%'):
        lprint(map(Host.Host,self.db.purgeHosts(addresses)))
    
    def addURL(self,url):
        split = list(filter(None, url.split('/')))
        proto = split[0].strip(':')
        host_part = split[1]
        path = '/'+'/'.join(split[2:])
        hsplit = host_part.split('@',2)
        if len(hsplit) == 2:
            cred = hsplit[0]
            socket = hsplit[1]
        else:
            cred = ''
            socket = hsplit[0]
        ssplit = socket.split(':',2)
        if len(ssplit) == 2:
            server = ssplit[0]
            port = ssplit[1]
        else:
            port = ''
            server = hsplit[0]
        csplit = cred.split(':',2)
        if len(csplit) == 2:
            user = csplit[0]
            password = csplit[1]
        else:
            password = ''
            user = csplit[0]

        return self.db.addURL(proto,user,password,server,port,path)
        


if __name__ == '__main__': sys.exit(100)
