# pylint: disable=bad-whitespace,bad-continuation,line-too-long,multiple-statements,trailing-whitespace,trailing-newlines,invalid-name,trailing-whitespace
# -*- coding: UTF-8 -*-
"""OSMDB configuration management."""
import sys
from json import loads, dumps
class Configuration():
    def __init__(self):
        self.configuration = {}
        self.filename = str(sys.argv[0])+'.conf'
        try:
            with open(self.filename,'r') as f:
                self.configuration = loads(f.read())
        except Exception as e:
            print('Can’t load configuration! ({})'.format(str(e)),file=sys.stderr)

if __name__ == '__main__': sys.exit(100)
