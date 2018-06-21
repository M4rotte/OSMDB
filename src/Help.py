import sys
from os import path


def helpAndExit(this):

    if this   == 'execute':   print('Usage: {} --execute <command>'.format(path.basename(sys.argv[0])), file=sys.stderr)
    elif this == 'selection': print('Usage: {} --selection <query>'.format(path.basename(sys.argv[0])), file=sys.stderr)
    exit(99)
