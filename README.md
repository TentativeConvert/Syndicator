# Syndicator
Dropbox-inspired indicator applet for real-time synchronization with Unison on Ubuntu 

## Prerequisites (overview)
1.  SSH access to a server via public key authentication
2.  A working installation of unison on the client and the server (version 2.48.3 or later)
3.  (optional) A working installation of a backup tool like back-in-time.

Brief details on how to set up each of these can be found further below.

## Installation/configuration

Download & adapt the relevant lines in `config.py` for your system.

## Prerequisites (instructions)
### ssh access to server via public key authentication
Generate public-private-keypair on your client with:
```
$ ssh-keygen -t rsa -b 4096
```
[Think about passphrase.]
There should now be one private key (id_rsa) and one public key (id_rsa.pub) in ~/.ssh.
Copy the public key to the server:
```
$  scp .ssh/id_rsa.pub username@server.address:/user-directory/.ssh/otherkeys
```
Append this public key to the file .ssh/authorized_keys on the server:
```
$  ssh username@server.address
$  cd ~/.ssh
$  cat otherkeys/id_rsa.pub >> authorized_keys
```
That's it (assuming the server is correctly configured).
More detailed instructions can be found here ...

### Unison
See: http://www.cis.upenn.edu/~bcpierce/unison/download/releases/stable/unison-manual.html

### Back-in-time
See: http://backintime.le-web.org/
