# pylint: disable=bad-whitespace,bad-continuation,line-too-long,multiple-statements,trailing-whitespace,trailing-newlines,invalid-name,trailing-whitespace
# -*- coding: UTF-8 -*-
"""OSMDB configuration management."""
import sys
import resource
from json import loads, dumps
class Configuration():
    def __init__(self):
        self.configuration = {}
        self.filename = str(sys.argv[0])+'.conf'
        try:
            with open(self.filename,'r') as f: self.configuration = loads(f.read())
            if not self.configuration.get('log_file', False):
                self.configuration['log_file'] = '&1'
        except Exception as e:
            print('Can’t load configuration, will be using default values! ({})'.format(str(e)),file=sys.stderr)
            self.configuration['log_file'] = '&1'
            self.configuration['ping_chunk_size'] = 32
            self.configuration['url']['chunk_size'] = 32
            self.configuration['ssh']['chunk_size'] = 32
            self.configuration['db_file'] = './osmdb.db'

        limit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
        if  limit < self.configuration['ping_chunk_size']:
            print('{} is too big as chunk size for ping. Setting to {}.'.format(self.configuration['ping_chunk_size'],limit))
            self.configuration['ping_chunk_size'] = limit
        if  limit < self.configuration['url']['chunk_size']:
            print('{} is too big as chunk size for URL check. Setting to {}.'.format(self.configuration['url']['chunk_size'],limit))
            self.configuration['url']['chunk_size'] = limit        
        if  limit < self.configuration['ssh']['chunk_size']:
            print('{} is too big as chunk size for SSH execution. Setting to {}.'.format(self.configuration['ssh']['chunk_size'],limit))
            self.configuration['ssh']['chunk_size'] = limit     
        if  limit < self.configuration['snmp']['chunk_size']:
            print('{} is too big as chunk size for SNMP check. Setting to {}.'.format(self.configuration['snmp']['chunk_size'],limit))
            self.configuration['snmp']['chunk_size'] = limit  

if __name__ == '__main__': sys.exit(100)
