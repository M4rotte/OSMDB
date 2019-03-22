import sys
from os import path


def helpAndExit(this):

    name = path.basename(sys.argv[0])
    if this   == 'execute':            print("""Usage: {name} --execute <command> [--selection <hosts selection query>]
 {name} --execute <command> [--tags <hosts tag selection>]""".format(name=name), file=sys.stderr)
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
    elif this == 'tag-hosts':          print("""Usage:\n {} --set-tag <tag> [--description <description>] <hosts selection query>
 {} --set-tag <tag> --selection <hosts selection query> --tags <tag query> [--description <description>]""".format(name,name), file=sys.stderr)
    elif this == 'set-param':          print("""Usage: {} --set-param <hostname|domain|*> <param>=<value>""".format(name), file=sys.stderr)
    elif this == 'get-param':          print("""Usage: {} --get-param <parameter> <hostname|domain>""".format(name), file=sys.stderr)
    elif this == 'deploy':             print("""Usage: {name} --deploy/-d <hosts selection query>""".format(name=name), file=sys.stderr)
    sys.exit(99)


def GeneralHelp():
    
    name = path.basename(sys.argv[0])
    print("""

The Overly Simple Management Database

Scan network for hosts:       {name} --update/-u host [--network/-n <network range>]
Update known hosts:           {name} --update/-u
Update known URLs:            {name} --update/-u url
Update host selection:        {name} --update/-u selection <hosts selection query>
List hosts using SQL:         {name} --selection/-s <hosts selection query>
List hosts using tags:        {name} --tags/-t <tag query>
Add host(s) in database:      {name} --add/-A host <hostname|address> [<hostname|address> …]
Tag host(s):                  {name} --set-tag/-T <tag> [--description <description>] <hosts selection query>
Tag host(s):                  {name} --set-tag <tag> --selection/-s <hosts selection query> --tags/-t <tag query> [--description <description>]
Add URL in database:          {name} --add/-A url <URL> [<URL> …]
Remove host(s) from database: {name} --delete/-D host --selection/-s <hosts selection query>
Remove URL(s) from database:  {name} --delete/-D url <URLs selection query>
Remove tag from host(s):      {name} --delete/-D tag <tag> <hosts selection query>
Execute command on host(s):   {name} --execute/-e <commande> --selection/-s <hosts selection query>
List last updates             {name} --list/-l update
List last executions:         {name} --list/-l execution
Set parameter for host(s):    {name} --set-param/-X <hostname|domain|*> <param>=<value>
Get parameters for host:      {name} --get-param/-x <parameter> <hostname|domain>
Deploy on host(s):            {name} --deploy/-d <hosts selection query>
Purge duplicated hosts        {name} --purge/-P <hosts selection query>

""".format(name=name), file=sys.stderr)

