import digital_ocean_manager
import SimpleSSH
import time
import sys

'''
Script to fix the Digital Ocean's old problem of not providing fingerprints for
newly created droplets, making you insecurely accept them or painly find them on
the slow and annoying web console. 

How it works?

You connect to an already known droplet (for which you get the fingerprints from the web
console, please do not accept the fingerprints for it blindly) that has private networking enabled, 
which we'll call 'base' droplet (if not in private network, enable it in dashboard for this droplet).

Then we create, through the API, a 'target' droplet with the private networking
enabled too (internal digital ocean's local networking) IN THE SAME REGION OF THE BASE DROPLET
(of course). Then we SSH to the 'base' droplet, and inside it, we run ssh-keyscan to the
'target' droplet via the local network, so we not get 'man in the middled' to retrieve the
fingerprints, which are printed on the screen.

This script can connect to the base droplet through password or ssh keys, just configurate
below. The target droplet will get all the ssh keys provided in the dashboard, but we 
don't even connect to the 'target' droplet, we just ssh-keyscan it locally from the 'base' 
droplet

'''

#user configuration--------------------------------
token = "" #Digital Ocean API token
name_base_droplet = ""
port_base_droplet = 22
username_base_droplet = "root"
password_base_droplet = ""
#If file path is set, password_base_droplet will be its password
key_filename_base_droplet = None
#Paste below base64 pub key or sha256 fingerprint of base droplet. Don't use MD5, it's insecure, update openssh instead
base_droplet_fingerprints = ["fingerprint_key_1", "fingerprint_key_2", "fingerprint_key_3", "..."] 
name_target_droplet = ""
create_droplet = True
target_droplet_config = {'region':'nyc3',
                         'image':'ubuntu-16-10-x64',
                         'size':'512mb',
                         'networking': True,
                         'backups': False}
#--------------------------------------------------
print('Connecting to Digital Ocean...\n')
manager = digital_ocean_manager.Manager(token)
base_droplet = manager.get_droplet(name=name_base_droplet)

if not create_droplet and not base_droplet: print('No target droplet found with name ' + name_target_droplet)
if create_droplet: 
    print('Creating droplet ' + name_target_droplet + "...")
    manager.create_droplet(name_target_droplet, target_droplet_config)
    print('Waiting for it to become active...')


target_droplet = manager.get_droplet(name=name_target_droplet)
if not target_droplet:
    print('Target droplet not found! Did you want to create it? If so, set create_droplet = True')
    exit()

#Waits for target droplet to become active, pass 'print' function
#to be executed on every try to verify if droplet is already active
def prtn(text):
    print(text, end='')
    sys.stdout.flush()
if not create_droplet: print('Verifying if droplet is active...')
manager.block_until_active(log=prtn, name=name_target_droplet)
print('')
if not manager.are_in_same_region(base_droplet, target_droplet):
    print('ERROR: base and target are not in the same region!')
    exit()

base_droplet_ip = manager.get_global_ip(base_droplet)
print('Base droplet ' + name_base_droplet + ' has IP ' + base_droplet_ip)
target_droplet_local_ip = manager.get_private_ip(target_droplet)
target_droplet_global_ip = manager.get_global_ip(target_droplet)
print('Target droplet ' + name_target_droplet + ' has global IP ' + target_droplet_global_ip + ' and local IP ' + target_droplet_local_ip + '\n')

print('SSHing to ' + base_droplet_ip + ':' + name_base_droplet + '...')
fingerprints_object = SimpleSSH.specify_fingerprints(base_droplet_fingerprints)
connection = SimpleSSH.SSHConnection(ip=base_droplet_ip, port=port_base_droplet,
                               username=username_base_droplet, password=password_base_droplet,
                               key_filename=key_filename_base_droplet,
                               policy=fingerprints_object)

print('Running ssh-keyscan from ' + base_droplet_ip + ':' + name_base_droplet + ' to ' + target_droplet_local_ip + ':' + name_base_droplet + ' LOCALLY...')
while True:
    scan = connection.remote_key_scan(target_droplet_local_ip)
    if not scan == None:
        break
    else:
        time.sleep(2)
print('sha256 fingerprints are:')
print(scan['sha256'])
