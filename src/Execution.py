# pylint: disable=bad-whitespace,bad-continuation,line-too-long,multiple-statements,trailing-whitespace,trailing-newlines,invalid-name,trailing-whitespace
# -*- coding: UTF-8 -*-
import sys
import time
from collections.abc import Mapping

class Execution(dict):

    def __init__(self, execution = None):
        
        super().__init__()
        self['user'] = execution[0]
        self['host'] = execution[1].fqdn
        self['cmdline'] = execution[2]
        self['return_code'] = execution[3]
        self['stdout'] = '\n'.join(execution[4]).strip()
        self['stderr'] = '\n'.join(execution[5]).strip()
        self['status'] = execution[6]
        self['start'] = execution[7]
        self['end'] = execution[8]

    def __repr__(self):
        
        handle = '{}@{}'.format(self['user'],self['host'])
        if len(self['stdout']) > 0: output = self['stdout'].split('\n')[0]
        elif len(self['stderr']) > 0: output = self['stderr'].split('\n')[0]
        else: output = self['status']
        if self['return_code'] == 0: status_symbol = '✓'
        elif self['return_code'] > 0: status_symbol = '❌'
        else: status_symbol = '⚠'
        return '{:32} {} {}'.format(handle, status_symbol, output)


if __name__ == '__main__': sys.exit(100)
