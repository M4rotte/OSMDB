import sys
from os import path


def helpAndExit(this):

    name = path.basename(sys.argv[0])
    if this   == 'execute':   print('Usage: {} --execute <command>'.format(name), file=sys.stderr)
    elif this == 'selection': print('Usage: {} --selection <query>'.format(name), file=sys.stderr)
    elif this == 'add':       print('Usage: {} --add <object type> <object 1> [<object 2> …]\nValid object types are: url, host'.format(name), file=sys.stderr)
    elif this == 'add-all':   print("""Usage:\n {} --add url <URL> [<URL> …]
 {} --add host <hostname|address> [<hostname|address> …]""".format(name,name), file=sys.stderr)
    elif this == 'add-url':   print("""Usage:\n {} --add url <URL> [<URL> …]""".format(name,name), file=sys.stderr)
    elif this == 'add-host':  print("""Usage:\n {} --add host <hostname|address> [<hostname|address> …]""".format(name,name), file=sys.stderr)
    elif this == 'list':      print('Usage: {} --list <object type>\nValid object types are: url, host, update, execution'.format(name), file=sys.stderr)
    exit(99)
