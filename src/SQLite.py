"""SQLite backend"""
import sys
import sqlite3
from time import time
from os import path
import datetime
import Logger

def humanTime(timestamp):
    try:
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        return datetime.datetime.fromtimestamp(0).strftime('%Y-%m-%d %H:%M:%S')

class SQLite:
    def __init__(self, configuration, logger = Logger.Logger()):
        
        try:
            self.logger = logger
            self.configuration = configuration
            self.configuration['ssh_default_user'] = self.configuration.get('ssh_default_user','root')
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

        execution_table = """CREATE TABLE IF NOT EXISTS execution (
                                       user TEXT,
                                       fqdn TEXT,
                                       cmdline TEXT,
                                       return_code INT,
                                       stdout,stderr TEXT,
                                       status TEXT,
                                       start,end FLOAT,
                                       FOREIGN KEY(fqdn) REFERENCES host(fqdn))"""
        
        self.cursor.execute(execution_table)

        url_table = """CREATE TABLE IF NOT EXISTS url (host TEXT,
                                       proto TEXT,
                                       path TEXT,
                                       port INT,
                                       user TEXT,
                                       password TEXT,
                                       check_time INTEGER,
                                       status TEXT,
                                       content TEXT,
                                       certificate TEXT,
                                       expire INT,
                                       PRIMARY KEY(proto,host,path,user,port))"""

        self.cursor.execute(url_table)

        host_tag_table = """CREATE TABLE IF NOT EXISTS host_tag (host TEXT,
                                       tag TEXT,
                                       description TEXT,
                                       tag_time INTEGER,
                                       FOREIGN KEY(host) REFERENCES host(fqdn),
                                       PRIMARY KEY(host, tag))"""

        self.cursor.execute(host_tag_table)
        
        self.connection.commit()

        host_view = """CREATE VIEW IF NOT EXISTS host_view AS SELECT fqdn, tag FROM
                                host INNER JOIN host_tag ON host.fqdn = host_tag.host"""

        self.cursor.execute(host_view)

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

    def addHost(self, hostname, fqdn, delay = -1, user = '', ip = ''):
        """Add a host in database if it doesn’t already exist."""
        if user == '': user = self.configuration['ssh_default_user']
        pre_query = """SELECT MAX(rowid) FROM host"""
        last_id = self.cursor.execute(pre_query).fetchone()[0]
        query = """INSERT OR IGNORE INTO host (hostname, fqdn, ping_delay, user, ip) VALUES (?,?,?,?,?)"""
        try:
            
            self.cursor.execute(query, (hostname, fqdn, delay, user, ip))
            if self.cursor.lastrowid > last_id:
                self.logger.log('Host “{}” inserted into database.'.format(hostname),0)
                self.connection.commit()
                return True
            else:
                print(self.listHosts('hostname LIKE "{}"'.format(hostname), seen_up=False)[0])
                return False
        except sqlite3.OperationalError as err:
            self.logger.log('Cant’t insert into host table! ({})'.format(err),12)
            return False
        except IndexError:
            pass
        except Exception as e:
            print(' **!!** '+str(e), file=sys.stderr)
            return False
        
    def hostUser(self,fqdn):
        query = """SELECT user FROM host WHERE fqdn = ?"""
        res = self.cursor.execute(query, (fqdn,)).fetchone()
        if res: return res[0]
        else: return self.configuration['ssh_default_user']
            
    def updateHosts(self, ping_delays, network_name = None):
        
        nb_up = nb_down = nb_new = nb_lost = nb_back = 0
        for hostname,fqdn,delay,ip in ping_delays:
            alive = self.hostAlive(hostname)
            seen_once = self.hostSeenOnce(hostname)
            user = self.hostUser(fqdn)
            self.addHost(hostname, fqdn, delay, user, ip)
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

    def listHosts(self, query, seen_up = True):
        
        if seen_up is True:
            if not query or query == '*': query = ''
            else: query = 'AND '+query
            query = 'SELECT * FROM host WHERE first_up NOT NULL {} ORDER BY last_change DESC'.format(query)
        else:
            if not query or query == '*': query = ''
            else: query = 'AND '+query
            query = 'SELECT * FROM host WHERE fqdn NOT NULL {} ORDER BY last_change DESC '.format(query)

        try: results = self.cursor.execute(query).fetchall()
        except (sqlite3.OperationalError,sqlite3.Warning): results = []
        hosts = []
        for record in results:
            hostname = record[0]
            if record[3] in [-1,'']: status = '❌'
            else: status = '✓'
            try: availability = record[11] * 100 / (record[11] + record[12])
            except ZeroDivisionError: availability = 0
            check = humanTime(record[5])
            if status == '❌':
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

    def hosts(self, query = '', status = 'UP'):

        if query == '*':
            if status is 'UP': query = """SELECT * FROM host WHERE ping_delay <> -1"""
            elif status is 'DOWN': query = """SELECT * FROM host WHERE ping_delay = -1"""
            elif status is 'ALL': query = """SELECT * FROM host"""
            else: query = """SELECT * FROM host WHERE first_up NOT NULL"""
        elif query is '':
            return []
        else:
            if status is 'UP': query = 'SELECT * FROM host WHERE first_up NOT NULL AND {}'.format(query)
            elif status is 'DOWN': query = 'SELECT * FROM host WHERE first_up IS NULL AND {}'.format(query)
            elif status is 'ALL': query = 'SELECT * FROM host WHERE {}'.format(query)
            else: query = 'SELECT * FROM host WHERE first_up NOT NULL WHERE {}'.format(query)
        try:
            return self.cursor.execute(query).fetchall()
        except (sqlite3.OperationalError,sqlite3.Warning) as e:
            self.logger.log('Misformed host selection query ({}). No host selected.'.format(e))
            return []

    def hostsByTags(self, query):

        final_query = 'WHERE '
        ored_queries = []
        try:
            for ored in query.split('|'):
                # ~ print('OR: '+ored)
                subquery = []
                for anded in ored.split('&'):
                    # ~ print('AND: '+ored)
                    query = 'SELECT fqdn FROM host_view WHERE '
                    for a in [anded]:
                        subquery.append('tag = "{}"'.format(a))
                    # ~ print('ANDedQueries: '+str(subquery))
                    query = ' AND '.join(subquery)
                ored_queries.append(query)
            # ~ print('ORedQueries: '+str(ored_queries))
            final_query = ' OR '.join(ored_queries)
            print('### '+final_query+' ###')
        except AttributeError: pass
        return []
        

    def addExecutions(self, executions):
        """Add executions in database."""
        query = """INSERT INTO execution (user,fqdn,cmdline,return_code,stdout,stderr,status,start,end) VALUES 
                         (:user,:host,:cmdline,:return_code,:stdout,:stderr,:status,:start,:end)"""
        try:
            self.cursor.executemany(query, executions)
            self.connection.commit()
            return True
        except sqlite3.OperationalError as err:
            self.logger.log('Cant’t insert into execution table! ({})'.format(err),12)
            return False
        except Exception as e:
            print(' **!!** '+str(e), file=sys.stderr)
            return False

    def listExecutions(self):
        
        query = """SELECT * FROM execution ORDER BY end DESC"""
        return self.cursor.execute(query).fetchall()
        
    def purgeHosts(self, addresses):
        query = """SELECT * FROM host WHERE ip LIKE ?"""
        hosts = self.cursor.execute(query, (addresses,)).fetchall()
        deleted = []
        for host in hosts:
            query = """SELECT fqdn,ip FROM host WHERE ip = ? ORDER BY last_check DESC"""
            _hosts = self.cursor.execute(query, (host[2],)).fetchall()
            if len(_hosts) < 2: continue
            else:
                ads = []
                for a in _hosts: ads.append(a[0])
                fqdn_list = ', '.join(ads)
                self.logger.log('Address “{}” has the following FQDNs: {}'.format(host[2],fqdn_list), 0)
                for h in _hosts[1:]:
                    self.logger.log('Delete host “{}” having IP {}'.format(h[0],h[1]), 1)
                    query = """DELETE FROM host WHERE fqdn = ?"""
                    self.cursor.execute(query, (h[0],))
                    deleted.append(host)
        self.connection.commit()
        return deleted

    def commit(self):
        try:
            self.connection.commit()
            self.logger.log('Committing to database.',0)
            return True
        except Exception as e:
            print(str(e), file=sys.stderr)
            return False

    def deleteExecutions(self, fqdn_list):
        if len(fqdn_list) == 0: return False
        ored = []
        for fqdn in fqdn_list:
            ored.append('fqdn = "{}"'.format(fqdn))
        query = 'DELETE FROM execution WHERE '+' OR '.join(ored)
        self.cursor.execute(query)

    def deleteHosts(self, fqdn_list):
        if len(fqdn_list) == 0: return False
        ored = []
        self.deleteExecutions(fqdn_list)
        for fqdn in fqdn_list:
            ored.append('fqdn = "{}"'.format(fqdn))
        query = 'DELETE FROM host WHERE '+' OR '.join(ored)
        self.logger.log('Deleting hosts: '+', '.join(fqdn_list),1)
        self.cursor.execute(query)

    def addURL(self, url):
        try:
            self.addHost(url[3], url[3], -1, '', '')
            query = """INSERT INTO URL (proto,user,password,host,port,path) VALUES (?,?,?,?,?,?)"""
            self.cursor.execute(query, url)
            self.connection.commit()
            return True
        except sqlite3.IntegrityError as e:
            return str(e)
            
    def urls(self):
        query = """SELECT * FROM url"""
        return self.cursor.execute(query).fetchall()
