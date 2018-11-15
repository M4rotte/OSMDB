import sys
from os import path


def helpAndExit(this):

    name = path.basename(sys.argv[0])
    if this   == 'execute':            print('Usage: {} --execute <command> [--selection <hosts selection query>]'.format(name), file=sys.stderr)
    elif this == 'selection':          print('Usage: {} --selection <hosts selection query>'.format(name), file=sys.stderr)
    elif this == 'selection-by-tag':   print('Usage: {} --tags <tag query>'.format(name), file=sys.stderr)
    elif this == 'add':                print('Usage: {} --add <object type> <object 1> [<object 2> …]\nValid object types are: host, url'.format(name), file=sys.stderr)
    elif this == 'add-all':            print("""Usage:\n {} --add host <hostname|address> [<hostname|address> …]
 {} --add url <URL> [<URL> …]""".format(name,name), file=sys.stderr)
    elif this == 'delete-all':         print("""Usage:\n {} --delete host <FQDN> [<FQDN> …]
 {} --delete host --selection <hosts selection query>
 {} --delete url <URLs selection query>
 {} --delete tag <tag> --selection <hosts selection query>""".format(name,name,name,name), file=sys.stderr)
    elif this == 'add-url':            print("""Usage:\n {} --add url <URL> [<URL> …]""".format(name,name), file=sys.stderr)
    elif this == 'add-host':           print("""Usage:\n {} --add host <hostname|address> [<hostname|address> …]""".format(name,name), file=sys.stderr)
    elif this == 'list':               print('Usage: {} --list <object type>\nValid object types are: host, execution, url, update'.format(name), file=sys.stderr)
    elif this == 'delete-url':         print('Usage: {} --delete url <URLs selection query>'.format(name), file=sys.stderr)
    elif this == 'delete-host':        print("""Usage:\n {} --delete host <FQDN> [<FQDN> …]
 {} --delete host --selection <hosts selection query>""".format(name,name,name), file=sys.stderr)
    elif this == 'delete-tag':         print('Usage: {} --delete tag <tag> <hosts selection query>'.format(name), file=sys.stderr)
    elif this == 'tag-hosts':          print("""Usage:\n {} --set-tag <tag> --description <description> <hosts selection query>
 {} --set-tag <tag> --selection <hosts selection query> --tags <tag query> --description <description>""".format(name,name), file=sys.stderr)
    elif this == 'set-param':          print("""Usage: {} --set-param <hostname|domain|*> <param>=<value>""".format(name), file=sys.stderr)
    elif this == 'get-param':          print("""Usage: {} --get-param <parameter> <hostname|domain>""".format(name), file=sys.stderr)
    sys.exit(99)


