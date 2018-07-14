# pylint: disable=bad-whitespace,bad-continuation,line-too-long,multiple-statements,trailing-whitespace,trailing-newlines,invalid-name,trailing-whitespace
# -*- coding: UTF-8 -*-
"""OSMDB"""
import sys
import ipaddress
import subprocess
import Host, Logger
import socket, requests
from multiprocessing import Process, Queue
from datetime import timedelta, datetime
from time import time
import ssl
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import Host, SSHClient, Execution, URL


def getDefaultRoute(): 
    """Call the external command `ip route`. This only works with Linux. The default route is used if no network is given in the command line (--network)."""
    return str(subprocess.check_output(['ip','route'], universal_newlines=True).splitlines()[1]).split(' ')[0]

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n): yield l[i:i + n]

def lprint(l):
    if type(l) is not list: l = list(l)
    for i in l: print(i)


def GetURL(url, q = Queue(), verify = False):
    """`url` is an URL.URL object. An URL.URL object is also both put in queue q and returned."""
    # TODO : 
    #  - make the use of user/password directly in URL optional
    #  - make the SSL validity verification optional
    if not url['port']: url['port'] = '443'
    url['check_time'] = int(time())
    try:
        ssl_cert = ssl.get_server_certificate((url['host'], int(url['port'])))
        url['certificate'] = ssl_cert
        cert = x509.load_pem_x509_certificate(bytes(ssl_cert,'utf-8'), default_backend())
        url['expire'] = cert.not_valid_after.strftime('%s')
        res = requests.get(repr(url), auth=(url['user'],url['password']), verify=verify)
        url['content'] = res.text
        url['status']  = res.status_code
        url['get_error']  = ''
    except Exception as e:
        print(str(e),file=sys.stderr)
        url['content'] = ''
        url['status']  = -1
        url['get_error'] = str(e)
    finally:
        q.put(url)
        return url

class OSMDB:
    """The Overly Simple Management Database main object."""
    def __init__(self, configuration, db, logger = Logger.Logger()):
        
        self.db = db
        self.configuration = configuration
        self.logger = logger
        self.configuration['ping_chunk_size'] = self.configuration.get('ping_chunk_size', 32)
        default_url_configuration = {
            'chunk_size': 2,
            'verify_ssl': 'False'
        }
        self.configuration['url'] = self.configuration.get('url', default_url_configuration)
        
    def __repr__(self): return 'OSMDB'
    
    def pingAddr(self, addresses):
        
        hosts = []
        remaining = len(addresses)
        queue = Queue(remaining)
        self.logger.log('Processing {} addresses in batches of {}.'.format(remaining, str(self.configuration['ping_chunk_size'])), 0)
        batch_index = 1
        start = time()
        try:
            for chunk in chunks(addresses, self.configuration['ping_chunk_size']):
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
    
    def pingHosts(self, network = '127.0.0.0/8'):
        """Ping all hosts in a given network and update the database. It returns the list
           of hosts, each host being a triplet (hostname, fqdn, ping_delay).
           If network is False the `ip route` external command will be called
           to get the default route and use it."""
        
        if not network: network = getDefaultRoute()
        try: net = ipaddress.IPv4Network(network)
        except ValueError as e:
            print('Invalid network specification: '+str(e), file=sys.stderr)
            return hosts
        addresses = list(net.hosts())
        return self.pingAddr(addresses)

    def pingAddresses(self, addresses = []):
        """Ping all addresses and update the database. It returns the list
           of hosts, each host being a triplet (hostname, fqdn, ping_delay)."""
        return self.pingAddr(addresses)

    def getURLs(self):
        
        _urls = []
        urls = list(map(URL.URL, self.db.urls()))
        self.logger.log('GET request on {} URLs in chunks of {}'.format(len(urls),self.configuration['url']['chunk_size']), 0)
        if self.configuration['url']['verify_ssl'] == 'True': verify = True
        else: verify = False
        for url_chunk in chunks(urls, self.configuration['url']['chunk_size']):
            queue = Queue(self.configuration['url']['chunk_size'])
            for url in url_chunk:
                self.logger.log('GET: {} …'.format(url), 0)
                Process(target=GetURL,args=((url,queue,verify))).start()
            for _ in range(0, len(url_chunk)):
                item = queue.get()
                self.logger.log('GET: {} [{}]'.format(item,item['status']), 0)
                _urls.append(item)

        return _urls
        
    
    def updateHosts(self, ping_delays, network_name = None): self.db.updateHosts(ping_delays, network_name)

    def updateURLs(self):
        try:
            urls = self.getURLs()
            self.db.updateURLs(urls)

        except TypeError:
            return False

    def execOnHosts(self,command='', hosts = []):
        _hosts = []
        for host in hosts:
            _hosts.append(self.db.hostByName(host))
        hosts = list(map(Host.Host, _hosts))
        executions = list(map(Execution.Execution, self.ssh.execute(command, hosts)))
        lprint(executions)
        self.db.addExecutions(executions)
    def listHosts(self, hosts):
        lprint(hosts)
    def listHostsByNames(self, hostnames):
        lprint(self.db.listHostsByName(hostnames))
    def listHostUpdates(self):
        lprint(self.db.listHostUpdates())
    def deploy(self, key, hosts):
        """Add the public key of OSMDB in the authorized_keys file of the given hosts."""
        if len(hosts) > 0: self.ssh.deploy(key, list(map(Host.Host,hosts)))
    def selectHosts(self, query = '', status = 'UP'):
        return self.db.hosts(query=query, status=status)
    def selectHostsByTags(self, tags = ''):
        return self.db.hostsByTags(tags)
    def listExecutions(self):
        for execution in self.db.listExecutions():
            execution_l = list(execution)
            execution_l[1] = Host.Host((execution[1],execution[1],None))
            execution_l[4] = execution[4].split('\n')
            execution_l[5] = execution[5].split('\n')
            print(Execution.Execution(execution_l))
    def purgeHosts(self, addresses = '%'):
        lprint(map(Host.Host,self.db.purgeHosts(addresses)))
    
    def addHost(self, hostname):
        fqdn = socket.getfqdn(hostname).lower()
        try: ip = socket.gethostbyname(hostname)
        except socket.gaierror as e:
            ip = ''
        self.db.addHost(hostname, fqdn, ip=ip)

    def deleteHosts(self, fqdn_list):

        self.db.deleteExecutions(fqdn_list)
        self.db.deleteHosts(fqdn_list)
        self.db.commit()

    def addURL(self,url):

        proto,user,password,server,port,path = URL.splitURL(url)
        if not server:
            print('Invalid URL: {}'.format(url))
            return False
        action = self.db.addURL((proto,user,password,server,port,path))
        if action != True:
            self.logger.log('Can’t add “{}”: {}'.format(url,action))
        else: self.logger.log('Added URL “{}“'.format(url))

    def listURL(self):
        return list(map(URL.URL, self.db.urls()))

if __name__ == '__main__': sys.exit(100)
