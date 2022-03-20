# Securely get fingerprint for Digital Ocean droplets

Script to fix the Digital Ocean's old problem of not providing fingerprints for
newly created droplets, making you insecurely accept them or painly find them on
the slow and annoying web console. 

# How it works?

You connect to an already known droplet (for which you get the fingerprints from the web
console, please do not accept the fingerprints for it blindly), that has private networking enabled, 
which we'll call 'base' droplet (if not in private network, enable it in dashboard for this droplet).
Then we create, through the API, a 'target' droplet with the private networking
enabled (internal digital ocean's local networking) IN THE SAME REGION OF THE BASE DROPLET
(of course). Then we SSH to the 'base' droplet, and inside it, we run ssh-keyscan to the
'target' droplet via the local network, so we not get 'man in the middled' to retrieve the
fingerprints, which are printed on the screen.

This script can connect to the base droplet through password or ssh keys, just configurate
below. The target droplet will get all the ssh keys provided in the dashboard, but we 
don't even connect to the 'target' droplet, we just ssh-keyscan it locally from the 'base' 
droplet

# Usage

Install `paramiko` (SSH client for python) and `python-digitalocean` (Digital Ocean python API client) with:

```pip3 install paramiko python-digitalocean```

Create or pick the 'base' droplet's on your Digital Ocean's dashboard and get its name.

For the 'base' droplet, you'll do the sacrifice of checking the fingerprints manually through the web console. Launch it, and then run, as described [here][1]:

```
cd /etc/ssh
for file in *sa_key.pub
do   ssh-keygen -lf $file
done
``` 

You'll get the fingerprints of the different keys your host has. Put them into `base_droplet_fingerprints` in one of the example's configuration part (currently there's just `create_check_fingerprint.py`). 

Configure the rest: if your base droplet is accessible through password (not recommended), insert the `password` and leave `key_filename_base_droplet = None`. If it's acessible through public key, then put the key's password in the `password` variable, and the path to the file (not the folder) in `key_filename_base_droplet`. Scpecify the name of the target droplet in `name_target_droplet` and specify if you want to create it or if it already exists in `create_droplet = True`. Don't forget to set up the `target_droplet_config` if you want to create your target droplet. Remember to put the same region as the base droplet.

Now just run

`python3 create_check_fingerprint.py`

[1]: http://www.phcomp.co.uk/Tutorials/Unix-And-Linux/ssh-check-server-fingerprint.html
