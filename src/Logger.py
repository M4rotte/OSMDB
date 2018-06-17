# pylint: disable=bad-whitespace,bad-continuation,line-too-long,multiple-statements,trailing-whitespace,trailing-newlines,invalid-name,trailing-whitespace
# -*- coding: UTF-8 -*-
"""OSMDB Logger."""
import sys
from time import strftime
from inspect import currentframe
class Logger:
    """Log messages."""
    def __init__(self):
        self.logfile  = sys.stderr
        self.log_time = False
        self.level = 0

    def __del__(self): self.logfile.close()

    def log(self, message, level = 0, f = None):
        """Write a message to the logger’s output if its criticity is over the chosen level."""
        prefix = ''
        info = '{}|{}'.format(str(level),str(currentframe().f_back.f_locals['self']))
        if self.log_time: prefix = '{} {:12s} '.format(strftime("%Y-%m-%d %H:%M:%S"),info)
        if level >= self.level:
            if f: print(prefix+str(message), file=f)
            else: print(prefix+str(message), file=self.logfile)
        self.flush()

    def setLogfile(self, filename):
        """Set Logger log file."""
        if filename == '&1': self.logfile = sys.stdout
        elif filename == '&2': self.logfile = sys.stderr
        else: self.logfile = open(filename,'a')

    def setLogLevel(self, level):
        """Set Logger minimum log level."""
        self.level = level
        
    def flush(self): self.logfile.flush()

    def purge(self):
        """Purge logs."""
        self.logfile.seek(0)
        self.logfile.truncate()

if __name__ == '__main__': sys.exit(100)
