"""SQLite backend"""
import sqlite3
from time import time
class SQLite:
    def __init__(self, configuration):
        self.connection = sqlite3.connect(configuration['db_file'])
        self.cursor = self.connection.cursor()
        self.initialize_db()

    def initialize_db(self):
        
        host_table_creation_query = """CREATE TABLE IF NOT EXISTS host (
                                                          hostname TEXT PRIMARY KEY,
                                                          fqdn TEXT,
                                                          ip TEXT,
                                                          ping_delay FLOAT DEFAULT -1,
                                                          first_up INT,
                                                          last_check INT,
                                                          last_up INT,
                                                          last_down INT,
                                                          last_change INT,
                                                          adjacent_up INT DEFAULT 0,
                                                          adjacent_down INT DEFAULT 0,
                                                          checks INT DEFAULT 0)"""
        self.cursor.execute(host_table_creation_query)
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
            if result[0] != -1: return True
            else: return False
        except IndexError: return False

    def addHost(self, hostname, fqdn = '', delay = -1):
        """Add a host in database if it doesn’t already exist. Field “hostname” assumed to be primary key, thus uniq."""
        query = """INSERT OR IGNORE INTO host (hostname, fqdn, ping_delay) VALUES (?,?,?)"""
        try:
            self.cursor.execute(query, (hostname, fqdn, delay))
            return True
        except Exception as e:
            print(' **!!** '+str(e))
            return False
            
    def updateHosts(self, ping_delays):
        
        for hostname,fqdn,delay in ping_delays:
            alive = self.hostAlive(hostname)
            seen_once = self.hostSeenOnce(hostname)
            self.addHost(hostname, fqdn, delay)
            query = """UPDATE host SET checks = checks + 1 WHERE hostname = ?"""
            self.cursor.execute(query, (hostname,))
            query = """UPDATE host SET ping_delay = ? WHERE hostname = ?"""
            self.cursor.execute(query, (delay, hostname))
            now = int(time())
            if delay is -1:
                if not alive:
                    # ~ print('Host “'+hostname+'” was dead and still is.')
                    query = """UPDATE host SET adjacent_down = adjacent_down + 1 WHERE hostname = ?"""
                    self.cursor.execute(query, (hostname,))
                    query = """UPDATE host SET last_down = ? WHERE hostname = ?"""
                    self.cursor.execute(query, (now, hostname))
                else:
                    print('Host “'+hostname+'” was alive but is dead now.')
                    query = """UPDATE host SET last_change = ? WHERE hostname = ?"""
                    self.cursor.execute(query, (now, hostname))
                    query = """UPDATE host SET adjacent_down = 1 WHERE hostname = ?"""
                    self.cursor.execute(query, (hostname,))
            else:
                query = """UPDATE host SET ping_delay = ? WHERE hostname = ?"""
                self.cursor.execute(query, (delay, hostname))
                if alive:
                    # ~ print('Host “'+hostname+'” was alive and still is.')
                    query = """UPDATE host SET adjacent_up = adjacent_up + 1 WHERE hostname = ?"""
                    self.cursor.execute(query, (hostname,))
                    query = """UPDATE host SET last_up = ? WHERE hostname = ?"""
                    self.cursor.execute(query, (now, hostname))
                else:
                    print('Host “'+hostname+'” was dead but is alive now.')
                    if not seen_once:
                        query = """UPDATE host SET first_up = ? WHERE hostname = ?"""
                        self.cursor.execute(query, (now, hostname))
                    query = """UPDATE host SET last_change = ? WHERE hostname = ?"""
                    self.cursor.execute(query, (now, hostname))
                    query = """UPDATE host SET adjacent_up = 1 WHERE hostname = ?"""
                    self.cursor.execute(query, (hostname,))                                        

        try: self.connection.commit()
        except Exception as e:
            print(' **!!** '+str(e))
            return False
        return True
