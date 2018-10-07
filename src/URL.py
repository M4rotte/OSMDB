# pylint: disable=bad-whitespace,bad-continuation,line-too-long,multiple-statements,trailing-whitespace,trailing-newlines,invalid-name,trailing-whitespace
# -*- coding: UTF-8 -*-
from __future__ import print_function
import sys
import time
import string
from SQLite import humanTime

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
        port = 443
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
            self['host']          = url[0]
            self['proto']         = url[1]
            self['path']          = url[2]
            self['port']          = url[3]
            self['user']          = url[4]
            self['password']      = url[5]
            self['check_time']    = url[6]
            self['response_time'] = url[7]
            self['total_time']    = url[8]
            self['status']        = url[9]
            self['headers']       = url[10]
            self['content']       = url[11]
            self['certificate']   = url[12]
            self['expire']        = url[13]
            self['get_error']     = url[14]

        except IndexError: pass # Let crash later…


    def __str__(self):
        
        output1 = self['proto']+'://'
        if self['user']: user = self['user']
        else: user = ''
        if self['password']: password = self['password']
        else: password = ''
        if user: output1 += user
        if password: output1 += ':'+password+'@'
        output1 += self['host']
        if self['port']: output1 += ':'+str(self['port'])
        output1 += self['path']
        return output1

    def __repr__(self):

        output1 = self['proto']+'://'
        if self['user']: user = self['user']
        else: user = ''
        if self['password']: password = self['password']
        else: password = ''
        if user: output1 += user
        if password: output1 += ':'+password+'@'
        output1 += self['host']
        if self['port']: output1 += ':'+str(self['port'])
        output1 += self['path']
        output2 = '[{}/{}]'.format(self['status'],self['response_time'])
        output3 = humanTime(self['expire'])
        return '{:<80} {:<20} Expire: {}'.format(output1, output2, output3)
        

if __name__ == '__main__': sys.exit(100)
