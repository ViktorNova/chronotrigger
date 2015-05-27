#!/usr/bin/env python3
# Switch to the next song in NSM when Jack transport reaches a certain point
# __author__ = 'Viktor Nova'

import nsmclient
# Including a copy of latest nsmclient from git master
#https://raw.githubusercontent.com/nilsgey/pynsmclient/master/nsmclient.py

import jack
# Including a copy of latest jack-client from git master
# https://raw.githubusercontent.com/spatialaudio/jackclient-python/master/jack.py

from time import sleep

client = jack.Client("chronotrigger")
client.activate()


#TODO: Go to the beginning of the song
jack.Client.transport_locate(client, 1)

#TODO: Start the transport
jack.Client.transport_start(client)



# Test - return a human readable time
while True:
    # Print everything for the hell of it
    transport = client.transport_query()
    print("Full JACK Transport Status: ", transport)

    status = client.transport_state
    print("Transport state is: ", status)

    bar = transport[1]['bar']
    print("Song position is: ", bar)
    sleep(1)


# TODO: Make this trigger on KILL and HUP as well
client.deactivate()
client.close()
