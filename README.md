# chronotrigger
NSM utility to automatically switch to the next song in your set list when JACK transport reaches a certain timestamp (Non Session Manager)



##Credits
chronotrigger uses these rad Python modules 
 -*pynsmclient*
 https://github.com/nilsgey/pynsmclient
 -*jack-client* 
 https://pypi.python.org/pypi/JACK-Client/
 
##Requirements
 - Python 3
 - liblo and pyliblo
 - jack-client (sudo pip3 install jack-client)
 - PyQt4 for optional GUI (will switch to a web UI soon)
 - NSM or something that uses NSM API v1.2