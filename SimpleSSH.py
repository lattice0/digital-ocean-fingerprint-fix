'''
Simple SSH connection module with fingerprint verification based on paramiko,
won't try to find SSH agents neither keys on computer, you provide your own.

See docs for paramiko here to learn about connection parameters used in this code:
http://docs.paramiko.org/en/2.1/api/client.html

I implemented a simple fingerprints rejection policy as explained in the docs. 
You pass a policy with a list of known fingerprints from the host. I recommend
putting all the fingerprints because you don't know key exchange protocol
will be used. Here's how to generate them:

http://www.phcomp.co.uk/Tutorials/Unix-And-Linux/ssh-check-server-fingerprint.html

'''

import paramiko
import hashlib
import base64
import re

#http://stackoverflow.com/a/5885097/6791424
base64_regex = '^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{4})$'

class Fingerprint():
        @staticmethod
        def to_md5(b64pubkey):
            md5 = hashlib.md5()
            md5.update(base64.b64decode(b64pubkey))
            hash_md5 = md5.digest()
            return hash_md5

        @staticmethod
        def to_sha_256(b64pubkey):
            sha256 = hashlib.sha256()
            sha256.update(base64.b64decode(b64pubkey))
            hash_sha256 = sha256.digest()
            return hash_sha256

        @staticmethod
        def to_base_64(plaintext):
            #Since it's fixed lenght always (sha256) we can take off the equals sign http://stackoverflow.com/a/9020716/6791424
            return str(base64.b64encode(plaintext), 'utf-8').replace('=', '')

        @staticmethod
        def is_base64_fingerprint(word):
            return bool(re.match(base64_regex, word))
        

#Interface to be passed to paramiko. Decides to reject or not a fingerprint
def specify_fingerprints(known_hosts):
    class MyPolicy(paramiko.MissingHostKeyPolicy):
        @staticmethod
        def missing_host_key(client, hostname, key):
            key64 = key.get_base64()
            fingerprint_sha256 = Fingerprint.to_base_64(Fingerprint.to_sha_256(key64))
            if fingerprint_sha256 in known_hosts:
                #print('Fingerprint accepted: ' + fingerprint)
                return
            else:
                raise ValueError('Fingerprint or public key REJECTED! Server ' + hostname +
                                 ' provided the following base 64 public key: ' + key64 +
                                 ' with the following SHA256 fingerprint: ' + fingerprint_sha256 +
                                 ' which is not in the provided list of fingerprints/keys.' + 
                                 'You provided the list: ' + str(known_hosts)
                                 )
    return MyPolicy

class SSHConnection():
    def __init__(self, **kwargs):
        self.ip = kwargs['ip']
        self.port = kwargs['port']
        if kwargs.__contains__('port'):
            self.port = kwargs['port']
        else:
            self.port = 22
        self.username = kwargs['username']
        self.password = kwargs['password']
        if kwargs.__contains__('key_filename'):
            self.key_filename = kwargs['key_filename']
        else:
            self.key_filename = None
        self.policy = kwargs['policy']
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(self.policy)
        self.ssh.connect(self.ip, port=self.port, username=self.username,
                         password=self.password, key_filename=self.key_filename,
                         allow_agent=False, look_for_keys=False)


    def execute(self, command):
        stdin,stdout,stderr = self.ssh.exec_command(command)
        outlines = stdout.readlines()
        resp = ''.join(outlines)
        return resp
    def execute_long(self,cmd):
        try:
            channel = self.ssh.invoke_shell()
            newline = '\n'
            channel.send(cmd + ' ; exit ' + newline)
            return channel
        except paramiko.SSHException as e:
            print(str(e))
    @staticmethod
    def for_each_line_of_channel(channel, do):
        line_buffer = ''
        channel_buffer = ''
        while True:
            channel_buffer = channel.recv(1).decode('UTF-8')
            if len(channel_buffer) == 0:
                break
            channel_buffer = channel_buffer.replace('\r', '')
            if channel_buffer != '\n':
                line_buffer += channel_buffer
            else:
                do(line_buffer)
                line_buffer = ''

    #Scans other machione through the connected one
    def remote_key_scan(self, ip):
        ssh_keyscan = self.execute('ssh-keyscan '+ ip)
        lines = ssh_keyscan.splitlines()
        no_comments = [lines[k] for k in range(len(lines)) if not lines[k].startswith('#')]
        base_64_keys = [no_comments[k].split(" ")[2] for k in range(len(no_comments))]
        if not len(base_64_keys)>0:
            return None
        sha256_fingerprints = [Fingerprint.to_base_64(Fingerprint.to_sha_256(x)) for x in base_64_keys]

        return {'sha256': sha256_fingerprints, 'base_64_public_keys': base_64_keys}
