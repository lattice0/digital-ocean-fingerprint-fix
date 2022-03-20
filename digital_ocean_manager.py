import digitalocean
import time

'''
Little manager for digital ocean droplets with little 
helper functions to get droplet names and IP's
'''

class Manager():
    def __init__(self, token, enforce_update = True):
        self.token = token
        self.manager = digitalocean.Manager(token=token)
        self.droplets = self.manager.get_all_droplets()
        self.keys = self.manager.get_all_sshkeys()
        self.enforce_update = enforce_update #Automatically updates droplets after some modification
    
    def update(self):
        if self.enforce_update: self.update_droplets()
    #@staticmethod
    def create_droplet(self, name, profile):
        region = profile['region']
        image = profile['image']
        size = profile['size']
        networking = profile['networking']
        backups = profile['backups']
        droplet = digitalocean.Droplet(token=self.token,
                                       name=name,
                                       region=region,
                                       image=image,
                                       size_slug=size,
                                       ssh_keys=self.keys,
                                       private_networking=networking,
                                       backups=backups)
        droplet.create()
        self.update()

    def update_droplets(self):
        self.droplets = self.manager.get_all_droplets()

    def ip_version(self, ip):
        return('v4')

    def get_droplet_by_name(self, name):
        return [self.droplets[x] for x in range(len(self.droplets)) 
                if name == self.droplets[x].name]

    def get_droplet_by_ip(self, ip):
        return [self.droplets[x] for x in range(len(self.droplets)) 
                if ip in str(self.droplets[x].networks[self.ip_version(ip=ip)])] #ADD SUPPORT FOR ANY IPVERSION

    def get_droplet(self, name=None, ip=None):
        droplets = digitalocean.Manager(token=self.token).get_all_droplets()

        if name: droplet = self.get_droplet_by_name(name)
        if ip: droplet = self.get_droplet_by_ip(ip)
        if len(droplet)>1:
            print("Warning! More than one droplet with same name, results may not be as you desire")
        if len(droplet)==0:
            return
        return droplet[0]

    def block_until_active(self, name=None, ip=None, log=None):
        while True:
            self.update_droplets()
            if log: log('.')
            droplet = self.get_droplet(name=name, ip=ip)
            if droplet.status == 'active': break
            time.sleep(3)

    def get_private_ip(self, droplet, ip_version='v4'):
        networks = droplet.networks[ip_version]
        return [networks[x]['ip_address'] for x in range(len(networks)) if networks[x]['type'] == 'private'][0]

    def get_global_ip(self, droplet, ip_version='v4'):
        networks = droplet.networks[ip_version]
        return [networks[x]['ip_address'] for x in range(len(networks)) if networks[x]['type'] == 'public'][0]

    def are_in_same_region(self, base_droplet, target_droplet):
        return base_droplet.region['slug'] == target_droplet.region['slug']
class Progress():
    def __init__(self):
        pass
    #prints at the same line
    def update(self, text):
        pass
