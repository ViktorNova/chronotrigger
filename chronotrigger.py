#!/usr/bin/env python3
# Switch to the next song in NSM when Jack transport reaches a certain point
# __author__ = 'Viktor Nova'

import nsmclient            # Local copy from latest git master: https://raw.githubusercontent.com/nilsgey/pynsmclient/master/nsmclient.py
import jack                 # Local copy from latest git master: https://raw.githubusercontent.com/spatialaudio/jackclient-python/master/jack.py
import os
import sys
from time import sleep
import argparse

# --------------------------------------------------------------------
# TEMPORARY SECTION - to make it work for the show
# TODO: Figure out how to actually use nsmclient.py


# Get song position to switch at and next song to automatically switch to
parser = argparse.ArgumentParser()
parser.add_argument("bar")      # First argument (Bar where song ends. When JACK transport reaches this bar, the song is considered to be over, and we will switch sessions and load the next song)
parser.add_argument("nextsong") # Second argument  (Name of the song we will automatically switch to when this song is finished)
args = parser.parse_args()

client = jack.Client("chronotrigger")
client.activate()

NSM_URL = os.getenv('NSM_URL')
#NSM_URL = "osc.udp://datakTARR:17545/" # for testing - change this to your current NSM url. This changes each time nsmd is launched, you can find it out by adding xterm to your session, then running "echo $NSM_URL"
if not NSM_URL:
    print("NSM_URL is not set, not running inside Non Session Manager, exiting")
    sys.exit()


print("NSM Daemon found at ", NSM_URL)

# Give clients a chance to load             TODO: Query nsmd to get all_clients_are_loaded = True instead (if running under NSM)
sleep(5)



# END TEMPORARY SECTION
# --------------------------------------------------------------------

#Go to the beginning of the song
jack.Client.transport_locate(client, 1)

#Start the transport
jack.Client.transport_start(client)

#####################################################

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
