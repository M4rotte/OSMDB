# pylint: disable=bad-whitespace,bad-continuation,line-too-long,multiple-statements,trailing-whitespace,trailing-newlines,invalid-name,trailing-whitespace
# -*- coding: UTF-8 -*-
"""OSMDB SNMP"""
import sys
try:
    from time import time
    from multiprocessing import Queue
    from pysnmp.hlapi import *
    import Logger

except ImportError as e:
    print(str(e), file=sys.stderr)
    print('Cannot find the module(s) listed above. Exiting.', file=sys.stderr)
    sys.exit(1)

def getSNMP(host, queue = Queue(), mib = 'SNMPv2-MIB', oid = 'sysDescr', community = 'public', port = '161', logger = Logger.Logger()):


    try:

        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   CommunityData(community, mpModel=0),
                   UdpTransportTarget((host, port)),
                   ContextData(),
                   ObjectType(ObjectIdentity(mib, oid, 0)))
        )

        if errorIndication:
            logger.log(host+': '+str(errorIndication), 3)
        elif errorStatus:
            logger.log('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'), 4)

        

        ret = varBinds[0].prettyPrint().split('=')[1].strip().replace('\n',' ').replace('\r',' ')
        queue.put((host,mib,oid,int(time()),ret))

    except BrokenPipeError as e:
        logger.log(host+': '+str(e),4)
        queue.put((host,mib,oid,int(time()),''))

    except IndexError as e:
        queue.put((host,mib,oid,int(time()),''))



