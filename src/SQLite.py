"""SQLite backend"""
import sqlite3
from time import time
from os import path
import datetime
import Logger
class SQLite:
    def __init__(self, configuration, logger = Logger.Logger()):
        
        try:
            self.logger = logger
            self.configuration = configuration
            self.connection = sqlite3.connect(self.configuration['db_file'])
            self.cursor = self.connection.cursor()
            self.initialize_db()
        except KeyError as e:
            print(str(e))
    
    def __repr__(self): return path.basename(self.configuration['db_file'])

    def initialize_db(self):
        host_table = """CREATE TABLE IF NOT EXISTS host (
                            hostname TEXT PRIMARY KEY,
                            fqdn TEXT,
                            ip TEXT,
                            ping_delay FLOAT DEFAULT -1,
                            first_up INT,
                            last_check INT,
                            last_up INT DEFAULT 0,
                            last_down INT DEFAULT 0,
                            last_change INT,
                            adjacent_up INT DEFAULT 0,
                            adjacent_down INT DEFAULT 0,
                            up INT DEFAULT 0,
                            down INT DEFAULT 0)"""
        
        self.cursor.execute(host_table)
        
        host_update_table = """CREATE TABLE IF NOT EXISTS host_update (
                                       update_time FLOAT,
                                       network TEXT,
                                       selection TEXT,
                                       up INT, down INT, back INT, lost INT, new INT,
                                       duration FLOAT)"""
        
        self.cursor.execute(host_update_table)
        
        self.connection.commit()

    def hostAlive(self, hostname):
        query = """SELECT ping_delay FROM host WHERE hostname = ?"""
        try:
            result = self.cursor.execute(query, (hostname,)).fetchall()[0]
            if result[0] != -1: return True
            else: return False
        except IndexError: return False

    def hostSeenOnce(self, hostname):
        query = """SELECT first_up FROM host WHERE hostname = ?"""
        try:
            result = self.cursor.execute(query, (hostname,)).fetchall()[0]
            if result[0] not in [-1, None]: return True
            else: return False
        except IndexError: return False

    def addHost(self, hostname, fqdn = '', delay = -1):
        """Add a host in database if it doesn’t already exist. Field “hostname” assumed to be primary key, thus uniq."""
        query = """INSERT OR IGNORE INTO host (hostname, fqdn, ping_delay) VALUES (?,?,?)"""
        try:
            self.cursor.execute(query, (hostname, fqdn, delay))
            return True
        except Exception as e:
            print(' **!!** '+str(e), file=sys.stderr)
            return False
            
    def updateHosts(self, ping_delays, network_name = None):
        
        nb_up = nb_down = nb_new = nb_lost = nb_back = 0
        for hostname,fqdn,delay in ping_delays:
            alive = self.hostAlive(hostname)
            seen_once = self.hostSeenOnce(hostname)
            self.addHost(hostname, fqdn, delay)
            start = time()
            now = int(start)
            query = """UPDATE host SET last_check = ? WHERE hostname = ?"""
            self.cursor.execute(query, (now, hostname))
            query = """UPDATE host SET ping_delay = ? WHERE hostname = ?"""
            self.cursor.execute(query, (delay, hostname))
            if delay is -1:
                nb_down += 1
                query = """UPDATE host SET down = down + 1 WHERE hostname = ?"""
                self.cursor.execute(query, (hostname,))
                if not alive:
                    # ~ print('Host “'+hostname+'” was dead and still is.')
                    query = """UPDATE host SET adjacent_down = adjacent_down + 1 WHERE hostname = ?"""
                    self.cursor.execute(query, (hostname,))
                    query = """UPDATE host SET last_down = ? WHERE hostname = ?"""
                    self.cursor.execute(query, (now, hostname))
                else:
                    nb_lost += 1
                    self.logger.log('Host “'+hostname+'” became unreachable.',2)
                    query = """UPDATE host SET last_change = ? WHERE hostname = ?"""
                    self.cursor.execute(query, (now, hostname))
                    query = """UPDATE host SET adjacent_down = 1 WHERE hostname = ?"""
                    self.cursor.execute(query, (hostname,))
            else:
                nb_up += 1
                query = """UPDATE host SET up = up + 1 WHERE hostname = ?"""
                self.cursor.execute(query, (hostname,))
                query = """UPDATE host SET ping_delay = ? WHERE hostname = ?"""
                self.cursor.execute(query, (delay, hostname))
                if alive:
                    # ~ print('Host “'+hostname+'” was alive and still is.')
                    query = """UPDATE host SET adjacent_up = adjacent_up + 1 WHERE hostname = ?"""
                    self.cursor.execute(query, (hostname,))
                    query = """UPDATE host SET last_up = ? WHERE hostname = ?"""
                    self.cursor.execute(query, (now, hostname))
                else:
                    
                    if not seen_once:
                        self.logger.log('Host “'+hostname+'” showed up for the first time.',1)
                        nb_new += 1
                        query = """UPDATE host SET first_up = ? WHERE hostname = ?"""
                        self.cursor.execute(query, (now, hostname))
                        query = """UPDATE host SET last_up = ? WHERE hostname = ?"""
                        self.cursor.execute(query, (now, hostname))
                        query = """UPDATE host SET adjacent_down = ? WHERE hostname = ?"""
                        self.cursor.execute(query, (0, hostname))
                        query = """UPDATE host SET down = ? WHERE hostname = ?"""
                        self.cursor.execute(query, (0, hostname))
                    else: 
                        nb_back += 1
                        self.logger.log('Host “'+hostname+'” is back.',1)   
                    query = """UPDATE host SET last_change = ? WHERE hostname = ?"""
                    self.cursor.execute(query, (now, hostname))
                    query = """UPDATE host SET adjacent_up = 1 WHERE hostname = ?"""
                    self.cursor.execute(query, (hostname,))                                        
        try:
            self.connection.commit()
            end = time()
            elapsed = str(datetime.timedelta(seconds=(end - start)))
            self.recordUpdate((time(), network_name, None, nb_up, nb_down, nb_back, nb_lost, nb_new, elapsed))
            self.logger.log('{} hosts updated in {} (UP:{} DOWN:{} BACK:{} LOST:{} NEW:{})'.format(len(ping_delays), elapsed, nb_up, nb_down, nb_back, nb_lost, nb_new), 1)
        except Exception as e:
            print(' **!!** '+str(e))
            return False
        return True

    def listHosts(self):
        
        query = """SELECT * FROM host WHERE first_up NOT NULL ORDER BY last_change DESC"""
        results = self.cursor.execute(query).fetchall()
        hosts = []
        for record in results:
            hostname = record[0]
            if record[3] == -1: status = 'DOWN'
            else: status = 'UP'
            availability = record[11] * 100 / (record[11] + record[12])
            check = datetime.datetime.fromtimestamp(record[5]).strftime('%Y-%m-%d %H:%M:%S')
            if status == 'DOWN':
                last = datetime.datetime.fromtimestamp(record[6]).strftime('%Y-%m-%d %H:%M:%S')
                last_nb = record[10]
            else:
                last = datetime.datetime.fromtimestamp(record[7]).strftime('%Y-%m-%d %H:%M:%S')
                last_nb = record[9]
            hosts.append('{:30s} {:4s}\t{}\t{}\t{}\t{:.6f}%'.format(hostname,status,check,last_nb,last,availability))  
        return hosts

    def recordUpdate(self, values):
        
        query = """INSERT INTO host_update (update_time, network, selection, up, down, back, lost, new, duration)
                    VALUES (?,?,?,?,?,?,?,?,?)"""
        self.cursor.execute(query, values)
        self.connection.commit()
