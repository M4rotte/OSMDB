# pylint: disable=bad-whitespace,bad-continuation,line-too-long,multiple-statements,trailing-whitespace,trailing-newlines,invalid-name,trailing-whitespace
# -*- coding: UTF-8 -*-
import sys
import time
import socket
import random
import struct
import select
from itertools import zip_longest

def chk(data):

    x = sum(x << 8 if i % 2 else x for i, x in enumerate(data)) & 0xFFFFFFFF
    x = (x >> 16) + (x & 0xFFFF)
    x = (x >> 16) + (x & 0xFFFF)
    return struct.pack('<H', ~x & 0xFFFF)

def ping(addr, timeout=5, number=1, data=b''):
    """ICMP ping."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as conn:
            payload = struct.pack('!HH', random.randrange(0, 65536), number) + data

            conn.connect((addr, 80))
            conn.sendall(b'\x08\0' + chk(b'\x08\0\0\0' + payload) + payload)
            start = time.time()
            while select.select([conn], [], [], max(0, start + timeout - time.time()))[0]:
                data = conn.recv(65536)
                if len(data) < 20 or len(data) < struct.unpack_from('!xxH', data)[0]:
                    continue
                if data[20:] == b'\0\0' + chk(b'\0\0\0\0' + payload) + payload:
                    return time.time() - start
            return -1
    except PermissionError as e: return tcp_connect(addr)
    except KeyboardInterrupt: return -1

def tcp_connect(addr, port = 22, timeout = 10):
    """TCP connect."""
    try:
        start = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((addr,port))
        s.close()
    except OSError as e:
        # If the error is one of the ones below then return connection time, else return -1
        # 111: Connection refused
        if e.errno not in [111]: return -1 
        else: return time.time() - start
    except KeyboardInterrupt: pass
    
    return time.time() - start

class Host:

    def __init__(self, host = None):
        
        if not host:
            self.address = '127.0.0.1'
            self.hostname = 'localhost'
            self.fqdn = 'localhost.localdomain'
        else:
            try:
                self.address = host[2]
                self.hostname = host[0]
                self.fqdn = host[1]
            except IndexError: pass
            try:
                self.ping = host[3]
                self.first = host[4]
            except IndexError: pass
            try:
                self.user = host[13]
            except IndexError: pass
            
    def process(self, address, queue):
    
        self.address = str(address)
        try:
            self.hostname = socket.gethostbyaddr(self.address)[0]
            self.fqdn = socket.getfqdn(self.hostname)
        except socket.herror:
            self.hostname = self.address
            self.fqdn = self.address
        finally:
            queue.put((self.hostname,self.fqdn,self.ping(),self.address))

    def __repr__(self):
        
        if self.fqdn: return self.fqdn
        else: return self.hostname

    def ping(self): return ping(self.address)

if __name__ == '__main__': sys.exit(100)
