"""SQLite backend"""
import sys
import sqlite3
from time import time
from os import path
import datetime
import Logger

def humanTime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

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
                            hostname TEXT,
                            fqdn TEXT PRIMARY KEY,
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
                            down INT DEFAULT 0,
                            user TEXT,
                            ssh_key_file TEXT)"""
        
        self.cursor.execute(host_table)
        
        host_update_table = """CREATE TABLE IF NOT EXISTS host_update (
                                       update_time FLOAT,
                                       network TEXT,
                                       selection TEXT,
                                       up INT, down INT, back INT, lost INT, new INT,
                                       duration FLOAT)"""
        
        self.cursor.execute(host_update_table)
        
        host_tag_table = """CREATE TABLE IF NOT EXISTS tag (host TEXT,
                                       tag TEXT,
                                       description TEXT,
                                       tag_time INTEGER,
                                       FOREIGN KEY(host) REFERENCES host(fqdn),
                                       PRIMARY KEY(host, tag))"""

        self.cursor.execute(host_tag_table)
        
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

    def addHost(self, hostname, fqdn, delay = -1):
        """Add a host in database if it doesn’t already exist."""
        query = """INSERT OR IGNORE INTO host (hostname, fqdn, ping_delay) VALUES (?,?,?)"""
        try:
            self.cursor.execute(query, (hostname, fqdn, delay))
            return True
        except sqlite3.OperationalError as err:
            self.logger.log('Cant’t insert into host table! ({})'.format(err),12)
            return False
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
            try:
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
            except sqlite3.OperationalError as err:
                self.logger.log('Cant’t update host table! ({})'.format(err),12)
                return False
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
            check = humanTime(record[5])
            if status == 'DOWN':
                last = humanTime(record[6])
                last_nb = record[10]
            else:
                last = humanTime(record[7])
                last_nb = record[9]
            hosts.append('{:30s} {:4s}\t{}\t{}\t{}\t{:.6f}%'.format(hostname,status,check,last_nb,last,availability))  
        return hosts

    def recordUpdate(self, values):
        
        query = """INSERT INTO host_update (update_time, network, selection, up, down, back, lost, new, duration)
                    VALUES (?,?,?,?,?,?,?,?,?)"""
        self.cursor.execute(query, values)
        self.connection.commit()

    def listHostUpdates(self):
        
        query = """SELECT * FROM host_update ORDER BY update_time DESC"""
        results = self.cursor.execute(query).fetchall()
        updates = []
        for record in results:
            update_time = humanTime(record[0])
            if not record[2]: source = record[1]
            else: source = record[2]
            updates.append('{} {:18} {}/{} {}/{}/{} {}'.format(update_time,source,record[3],record[4],record[5],record[6],record[7],record[8]))
        return updates

    def hosts(self, status = 'UP', query = ''):
        
        if not query:
            if status is 'UP': query = """SELECT * FROM host WHERE ping_delay <> -1"""
            elif status is 'DOWN': query = """SELECT * FROM host WHERE ping_delay = -1"""
            else: query = """SELECT * FROM host WHERE first_up NOT NULL"""
        elif query == '*':
            query = 'SELECT * FROM host WHERE first_up NOT NULL'
        else:
            query = 'SELECT * FROM host WHERE first_up NOT NULL AND {}'.format(query)
        try: return self.cursor.execute(query).fetchall()
        except sqlite3.OperationalError as e:
            self.logger.log('SQLite operational error! ({})'.format(e))
            return []
