#!/usr/bin/env python3
# Switch to the next song in NSM when Jack transport reaches a certain point
# __author__ = 'Viktor Nova'
# from _ast import arg
import liblo

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
parser.add_argument("endbar")   # First argument (Bar where song ends. When JACK transport reaches this bar, the song is considered to be over, and we will switch sessions and load the next song)
parser.add_argument("nextsong") # Second argument  (Name of the song we will automatically switch to when this song is finished)
args = parser.parse_args()

endbar = int(args.endbar)
nextsong = args.nextsong

NSM_URL = os.getenv('NSM_URL')
if not NSM_URL:
    print("NSM_URL is not set, not running inside Non Session Manager, exiting")
    sys.exit()
#NSM_URL = "osc.udp://datakTARR:11046/" # for debuging - change this to your current NSM url. This changes each time nsmd is launched, you can find it out by adding xterm to your session, then running "echo $NSM_URL"


print("NSM Daemon found at ", NSM_URL)

# Connect to JACK server
client = jack.Client("chronotrigger")
client.activate()

# Go to the beginning of the song
jack.Client.transport_locate(client, 1)
bar = 1



# END TEMPORARY SECTION
# --------------------------------------------------------------------

print("Current song position: Bar ", bar)
print("Song ends at bar ", endbar)
print("Switching to next song '", nextsong, "' in ", (endbar - bar), "bars")

# Give clients a chance to load   TODO: Query nsmd to get all_clients_are_loaded = True instead (if running under NSM)
sleep(5)

# Start the transport
print("STARTING TRANSPORT")
jack.Client.transport_start(client)

# Wait for the song to end
while bar < endbar:
    print(" ")
    # Print everything for the hell of it
    transport = client.transport_query()
    bar = transport[1]['bar']
    # print("Full JACK Transport Status: ", transport)

    status = client.transport_state
    print("Transport state is: ", status)

    print("Current song position: Bar ", bar)
    print("Song ends at bar ", endbar)
    print("Switching to next song '", nextsong, "' in ", (endbar - bar), "bars")
    sleep(1)

print()
print("Song is over.")
print("Disconnecting from JACK")

# TODO: Make this trigger on KILL and HUP as well
client.deactivate()
client.close()

print("Closing session and loading next song '", nextsong, "' NOW!")

message = liblo.Message("/nsm/server/open", nextsong)
print(message)
liblo.send(NSM_URL, message)
