# pylint: disable=bad-whitespace,bad-continuation,line-too-long,multiple-statements,trailing-whitespace,trailing-newlines,invalid-name,trailing-whitespace
# -*- coding: UTF-8 -*-
"""OSMDB commandline management."""
class Cmdline:
    def __init__(self, args = [], translations = {'--help':'-h'}):
        """Create a dictionnary of options and a list of tags. Tags are the elements of the argument array which are not an option nor an option value."""
        self.options = {}
        self.tags = []
        opt = False
        self.translations = translations
        for a in args[1:]:
            a = self.translateOption(a)
            if a[0] is '-':
                opt = ''.join(a[1:])
                self.options[opt] = {}
            elif opt:
                self.options[opt] = a
                opt = False
            else: self.tags.append(a)

    def translateOption(self, arg):
        """Translate a long option into its short version."""
        for k,v in self.translations.items():
            if arg == k: return v
        return arg

    def option(self,key):
        """Return option value, or True if option has no value, or False if option is absent."""
        try:
            if self.options[key] != {}: return self.options[key]
            else: return True
        except KeyError: return False
    
    def lastTag(self):
        """Return the last tag."""
        try: return self.tags[-1:][0]
        except IndexError: return False

    def listOptions(self):
        for o,v in self.options.items(): yield str(o)

    def dump(self):
        """Print the Option object to stdout."""
        print('OPTIONS  : '+str(self.options))
        print('TAGS     : '+str(self.tags))
        print('LAST TAG : '+str(self.lastTag()))

if __name__ == '__main__': sys.exit(100)
