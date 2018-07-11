# pylint: disable=bad-whitespace,bad-continuation,line-too-long,multiple-statements,trailing-whitespace,trailing-newlines,invalid-name,trailing-whitespace
# -*- coding: UTF-8 -*-
from __future__ import print_function
import sys
import time
import string
from multiprocessing import Queue

def splitURL(url):
    split = list(filter(None, url.split('/')))
    if ':' in split[0]:
        proto = split[0].strip(':')
        host_part = split[1]
    else:
        host_part = split[0]
        proto = 'https'
                
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
    
    return (proto,user,password,server,port,path)

class URL(dict):

    def __init__(self, url = None):

        try:
            super().__init__()
            self['host'] = url[0]
            self['proto'] = url[1]
            self['path'] = url[2]
            self['port'] = url[3]
            self['user'] = url[4]
            self['password'] = url[5]
            self['check_time'] = url[6]
            self['status'] = url[7]
            self['headers'] = url[8]
            self['content'] = url[9]
            self['certificate'] = url[10]
            self['expire'] = url[11]
            self['get_error'] = url[12]
        except IndexError: pass # Let crash later…

    def __repr__(self):

        output = self['proto']+'://'
        if self['user']: output += self['user']
        if self['password']: output += ':@'
        output += self['host']
        if self['port']: output += ':'+str(self['port'])
        output += self['path']
        return output

if __name__ == '__main__': sys.exit(100)
