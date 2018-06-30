import sys
from os import path


def helpAndExit(this):

    name = path.basename(sys.argv[0])
    if this   == 'execute':            print('Usage: {} --execute <command> [--selection <query>]'.format(name), file=sys.stderr)
    elif this == 'selection':          print('Usage: {} --selection <query>'.format(name), file=sys.stderr)
    elif this == 'selection-by-tag':   print('Usage: {} --tags <tag query>'.format(name), file=sys.stderr)
    elif this == 'add':                print('Usage: {} --add <object type> <object 1> [<object 2> …]\nValid object types are: host, url'.format(name), file=sys.stderr)
    elif this == 'add-all':            print("""Usage:\n {} --add host <hostname|address> [<hostname|address> …]
 {} --add url <URL> [<URL> …]""".format(name,name), file=sys.stderr)
    elif this == 'delete-all':         print("""Usage:\n {} --delete host <FQDN> [<FQDN> …] [--selection <query>]
 {} --delete url <URL> [<URL> …]""".format(name,name), file=sys.stderr)
    elif this == 'add-url':            print("""Usage:\n {} --add url <URL> [<URL> …]""".format(name,name), file=sys.stderr)
    elif this == 'add-host':           print("""Usage:\n {} --add host <hostname|address> [<hostname|address> …]""".format(name,name), file=sys.stderr)
    elif this == 'list':               print('Usage: {} --list <object type>\nValid object types are: host, execution, url, update'.format(name), file=sys.stderr)
    elif this == 'delete':             print('Usage: {} --delete <object type> <object 1> [<object 2> …] [--selection <query>]\nValid object types are: host, url'.format(name), file=sys.stderr)
    exit(99)


