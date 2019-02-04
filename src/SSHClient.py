# pylint: disable=bad-whitespace,bad-continuation,line-too-long,multiple-statements,trailing-whitespace,trailing-newlines,invalid-name,trailing-whitespace
# -*- coding: UTF-8 -*-
"""PCM SSH client."""
import sys
try:
    from os import chmod
    from multiprocessing import Process, Queue
    from cryptography.hazmat.primitives import serialization as crypto_serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend as crypto_default_backend
    from time import time, strftime

    from hashlib import blake2b
    from signal import SIGALRM
    from time import time
    import paramiko
    from socket import timeout
    from io import StringIO
    import signal
    from getpass import getpass
    from binascii import b2a_base64

except ImportError as e:
    print(str(e), file=sys.stderr)
    print('Cannot find the module(s) listed above. Exiting.', file=sys.stderr)
    sys.exit(1)

def chunks(l, n):
    """Yield successive n-sized chunks from list l."""
    for i in range(0, len(l), n): yield l[i:i + n]

class WithdrawException(Exception):
    
    def __init__(self, message): super().__init__(message)

class SSHClient:
    """SSH client."""

    def __init__(self, logger = None, configuration = None):
        """The SSH client is initialized from default key. A new key is generated if none exists."""

        self.configuration = configuration
        default_ssh_configuration = {
            'client_timeout': 30,
            'auth_timeout': 30,
            'banner_timeout': 30,
            'exec_timeout': 60,
            'default_key': './osmdb_id',
            'default_pubkey': './osmdb_id.pub'
        }
        self.configuration['ssh'] = self.configuration.get('ssh', default_ssh_configuration)
        self.configuration['exec_timeout'] = self.configuration.get('exec_timeout', 60)
        self.logger = logger
        self.rsakey = self.savedKey(self.configuration['ssh']['default_key'])
        try: self.key = self.rsakey.key
        except AttributeError: self.key = None
        if not self.key: self.newkey()
        message = 'Using key "{}"'.format(self.keyhash())
        logger.log(message, 1)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.load_system_host_keys()

    def __str__(self):
        return 'SSH'

    def handleSignal(self, signum, frame):
        
        if signum == SIGALRM: raise WithdrawException('Execution was still running after {} seconds.'.format(self.configuration['exec_timeout']))
        else: raise Exception('Signal: '+str(signum)+' at: '+str(frame))

    def newkey(self):
        """Generate a RSA key."""
        self.logger.log('Generating new key…', 1)
        self.key = rsa.generate_private_key(backend=crypto_default_backend(),public_exponent=65537,key_size=2048)
        self.saveKey(self.configuration['ssh']['default_key'],self.configuration['ssh']['default_pubkey'])

    def pubkey(self):
        """Return the public key."""
        if self.rsakey: return self.rsakey.get_base64()
        else: return None


    def privkey(self):
        """Return the private key."""
        return self.key.private_bytes(crypto_serialization.Encoding.PEM,crypto_serialization.PrivateFormat.TraditionalOpenSSL,crypto_serialization.NoEncryption())

    def sshkey(self):
        k = paramiko.RSAKey.from_private_key(StringIO(self.privkey().decode('utf-8')),password=None)
        return k

    def saveKey(self, keyfile, pubkeyfile):
        """Write the key pair to files."""

        with open(keyfile, 'wb') as f:
            f.write(self.key.private_bytes(encoding=crypto_serialization.Encoding.PEM,
                    format=crypto_serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=crypto_serialization.NoEncryption()))
        chmod(keyfile, 0o600)
        with open(pubkeyfile, 'wb') as f: f.write(self.key.public_key().public_bytes(crypto_serialization.Encoding.OpenSSH, \
    crypto_serialization.PublicFormat.OpenSSH))
        

    def savedKey(self, keyfile):
        """Get private key from file."""
        try:
            return paramiko.RSAKey.from_private_key_file(keyfile)
        except FileNotFoundError:
            return None

    def keyhash(self):
        """Return public key’s hash."""
        h = blake2b()
        h.update(self.key.public_key().public_bytes(crypto_serialization.Encoding.OpenSSH, \
    crypto_serialization.PublicFormat.OpenSSH))

        return h.hexdigest()

    def _execute(self, host, cmdline, q):
        """Execute a command on a host and put the result in a queue."""
        start  = time()
        try:
            exec_status = ''
            return_code = 0
            self.client.connect(host.hostname, username=host.user, pkey=self.sshkey(), timeout=float(self.configuration['ssh']['client_timeout']),
                                banner_timeout=float(self.configuration['ssh']['banner_timeout']), auth_timeout=float(self.configuration['ssh']['auth_timeout']))
            std    = self.client.exec_command(cmdline, timeout=float(self.configuration['ssh']['exec_timeout']))
            signal.alarm(int(self.configuration['exec_timeout']))
            signal.signal(signal.SIGALRM, self.handleSignal)
            self.logger.log('{}@{}> {}'.format(host.user,host.hostname,cmdline), 0)
            return_code = std[1].channel.recv_exit_status()
            stdout = list(std[1])
            stderr = list(std[2])
            end    = time()
            q.put((host.user, host, cmdline, return_code, stdout, stderr, exec_status, start, end))
            self.client.close()

        except (paramiko.ssh_exception.AuthenticationException,
                paramiko.ssh_exception.NoValidConnectionsError,
                paramiko.ssh_exception.SSHException,
                timeout,OSError,EOFError,ConnectionResetError,AttributeError) as error:
            end = time()
            self.logger.log('[{}@{}] `{}` {}'.format(host.user,host.hostname,cmdline,error),3)
            q.put((host.user , host, cmdline, -1, [], [], str(error), start, end))
            self.client.close()
            return False
            
        except WithdrawException as error:

            end = time()
            exec_status = 'Execution discarded: {}'.format(error)
            self.logger.log('[{}@{}] `{}` {}'.format(host.user, host.hostname, cmdline, exec_status),3)
            q.put((host.user, host, cmdline, -2, [], [], 'Execution discarded: {}'.format(error), start, end))
            self.client.close()
            return False  

        return True

    def hostUser(self,hostname):
        """Return the user to use for a given host. TODO: check in database for overriding."""
        return self.configuration['ssh']['default_user']

    def execute(self, cmdline, hosts):
        """Execute a command on hosts in parallel."""
        q = Queue()
        runs = []
        processes = []
        if cmdline is '': return []
        try: chunk_size = int(self.configuration['ssh']['chunk_size'])
        except KeyError: chunk_size = 4
        self.logger.log('Executing `{}` on {} hosts in chunks of {} hosts.'.format(cmdline,len(hosts),chunk_size),0)
        chunk_k = 1
        for chunk in chunks(hosts, chunk_size):
            nb_hosts = len(chunk)
            self.logger.log('Chunk #{:<3} {}'.format(chunk_k,', '.join(map(str,chunk))),0)
            for host in chunk:
                host.user = self.configuration['ssh']['default_user']
                proc = Process(target=self._execute, args=(host, cmdline, q))
                proc.start()
                processes.append(proc)
            for p in processes: p.join()
            for _ in range(0, nb_hosts):
                runs.append(q.get())
            chunk_k += 1

        return runs

    def executeScripts(self, hostname, scripts):
        """Copy and execute some shell scripts on a host."""
        try:
            executions = []
            user = self.hostUser(hostname)
            transport = paramiko.Transport((hostname, 22))
            transport.connect(username=user, pkey=self.sshkey())
            sftp = paramiko.SFTPClient.from_transport(transport)
            for script in scripts:
                localname = self.configuration['host_dir']+'/'+hostname+'/'+script+'.sh'
                remotename = '/tmp/'+script+'.sh'
                sftp.put(localname, remotename)
                executions.append(self.execute('sh '+remotename, [hostname]))
                sftp.remove(remotename)
            sftp.close()
            transport.close()
            return executions

        except (paramiko.ssh_exception.AuthenticationException,
                paramiko.ssh_exception.NoValidConnectionsError,
                paramiko.ssh_exception.SSHException,
                timeout,OSError,EOFError,ConnectionResetError,AttributeError) as error:

            self.logger.log('['+user+'@'+hostname+'] `'+str(scripts)+'` '+str(error),3)
            try:
                sftp.close()
                transport.close()
            except Exception: pass
            self.client.close()
            return [(user, hostname, scripts, str(error))]

    def _deploy(self, key, user, host, password, q):
        """Connect to remote host using password, to put the client key in ~/.ssh/authorized_keys.
           Put result in queue.
           It roughly works like the "ssh-copy-id" OpenSSL command."""
        pubkey = self.pubkey()
        start = time()
        exec_status = ''
        return_code = 0
        try:

            self.client.connect(host.hostname, username=user, password=password, timeout=float(self.configuration['ssh']['client_timeout']),
                                                                        banner_timeout=float(self.configuration['ssh']['banner_timeout']),
                                                                        auth_timeout=float(self.configuration['ssh']['auth_timeout']))

            self.client.exec_command('mkdir .ssh', timeout=float(self.configuration['ssh']['exec_timeout']))
            self.client.exec_command('chmod 0700 .ssh', timeout=float(self.configuration['ssh']['exec_timeout']))
            self.client.exec_command('echo "ssh-rsa '+pubkey+' ## OSMDB KEY ## '+strftime("%Y-%m-%d %H:%M:%S")+'" >> .ssh/authorized_keys', \
                                              timeout=float(self.configuration['ssh']['exec_timeout']))
            std = self.client.exec_command('chmod 0600 .ssh/authorized_keys', timeout=float(self.configuration['exec_timeout']))
            signal.alarm(int(self.configuration['exec_timeout']))
            signal.signal(signal.SIGALRM, self.handleSignal)
            stdout = list(std[1])
            stderr = list(std[2])
            return_code = std[1].channel.recv_exit_status()

            end = time()
            self.logger.log('Key {} deployed for {}@{}'.format(b2a_base64(key.get_fingerprint()).decode('utf-8').strip(),user,host.hostname),1)
            q.put((user, host, return_code, stdout, stderr, exec_status, start, end))
            self.client.close()
            return True

        except (paramiko.ssh_exception.AuthenticationException,
                paramiko.ssh_exception.NoValidConnectionsError,
                paramiko.ssh_exception.SSHException,
                timeout,OSError,EOFError,ConnectionResetError,AttributeError)  as e:
            
            end = time()
            self.logger.log('Error in deployement for {}@{}: {}'.format(user, host, e), 3)
            q.put((user, host, -1, [], [], str(e), start, end))
            self.client.close()
            return False

        except WithdrawException as error:

            end = time()
            self.logger.log('Deployement for {}@{} reached timemout! ('+str(error)+')',3)
            q.put((user, host, -2, [], [], str(error), start, end))
            self.client.close()
            return False  

    def deploy(self, key, hosts):
        
        q = Queue()
        runs = []
        processes = []
        try: chunk_size = int(self.configuration['ssh']['chunk_size'])
        except KeyError: chunk_size = 4
        self.logger.log('Deploying key {} on {} hosts in chunks of {} hosts.'.format(b2a_base64(key.get_fingerprint()).decode('utf-8').strip(),len(hosts),chunk_size),0)
        chunk_k = 1
        password = getpass('Password: ')
        for chunk in chunks(hosts, chunk_size):
            nb_hosts = len(chunk)
            self.logger.log('Chunk #{:<3} {}'.format(chunk_k,', '.join(map(str,chunk))),0)
            for host in chunk:
                proc = Process(target=self._deploy, args=(key, host.user, host, password, q))
                proc.start()
                processes.append(proc)
            for p in processes: p.join()
            for _ in range(0, nb_hosts):
                runs.append(q.get())
            chunk_k += 1

        return runs
