#!/usr/bin/env python3
# Switch to the next song in NSM when Jack transport reaches a certain point
# __author__ = 'Viktor Nova'
# from _ast import arg

import os


# for debuging - uncomment the os.environ line and
# change the value to your current NSM url.
# This changes each time nsmd is launched, you can find it out by adding xterm to your session, then running "echo $NSM_URL"
os.environ["NSM_URL"] = "osc.udp://datakTARR:11635/"

import liblo
import nsmclient            # Local copy from latest git master: https://raw.githubusercontent.com/nilsgey/pynsmclient/master/nsmclient.py
import jack                 # Local copy from latest git master: https://raw.githubusercontent.com/spatialaudio/jackclient-python/master/jack.py

import sys
from time import sleep
# import argparse

# Get song position to switch at and next song to automatically switch to
# parser = argparse.ArgumentParser()
# parser.add_argument("endbar")   # First argument (# Bar where song ends. When JACK transport reaches this bar, the song is considered to be over, and we will switch sessions and load the next song)
# parser.add_argument("nextsong") # Second argument  (Name of the song we will automatically switch to when this song is finished)
# args = parser.parse_args()

# TODO: this might need to change or disappear now
NSM_URL = os.getenv('NSM_URL')
if not NSM_URL:
    print("NSM_URL is not set, not running inside Non Session Manager, exiting")
    sys.exit()

print("NSM Daemon found at ", NSM_URL)

# END TEMPORARY SECTION
# --------------------------------------------------------------------

# [[[[[ NSM CLIENT SECTION ]]]]] -------------------------------------

capabilities = {
    "switch" : False,		# client is capable of responding to multiple `open` messages without restarting
    "dirty" : False, 		# client knows when it has unsaved changes
    "progress" : True,		# client can send progress updates during time-consuming operations
    "message" : True, 		# client can send textual status updates
    "optional-gui" : True,	# client has an optional GUI
    }

def myLoadFunction(pathBeginning, clientId):
    # TODO: If config file doesn't exist, create one
    # TODO: If config file is invalid, send an error message
    import configparser
    config = configparser.ConfigParser()
    config.sections()
    sessionpath = os.path.split(pathBeginning)[0]   # Strips out the serialized directory name since we can only have one instance

    print()
    print("-------- VIKTOR DEBUG SECTION --------")
    print("DEBUG:  Session Name (prettyNSMName) = ", nsmclient.states.prettyNSMName)
    print("DEBUG:  pathBeginning = ", pathBeginning)
    print("DEBUG:  Session path is = ", sessionpath)

    pathBeginning = sessionpath

    print()

    # Read config
    configfile = (pathBeginning + "/chronotrigger.conf")
    print("DEBUG:  Opening = ", configfile)
    config.read(configfile)
    endbar = int(config['NEXTSONG']['endbar'])
    print("endbar = ", endbar)
    nextsong = config['NEXTSONG']['nextsong']
    return True, "chronotrigger.conf"



def mySaveFunction(pathBeginning):
    print("-------- SAVE  DEBUG SECTION --------")
    """Pretend to save a file"""
    print("In the Save function, pathBeginning = ", pathBeginning)
    pathBeginning = os.path.split(pathBeginning)[0]
    print("so I override it again", pathBeginning)
    print("Did that work?")
    if True:
        return False, " ".join(["/".join([pathBeginning, "chronotrigger.conf"]), "has failed to save because an RNG went wrong"])
    else:
        return True, "chronotrigger.conf"
        # TODO: Get user options and save it
        # https://docs.python.org/3/library/configparser.html


requiredFunctions = {
    "function_open" : myLoadFunction,  # Accept two parameters. Return two values. A bool and a status string. Otherwise you'll get a message that does not help at all: "Exception TypeError: "'NoneType' object is not iterable" in 'liblo._callback' ignored"
    "function_save" : mySaveFunction,  # Accept one parameter. Return two values. A bool and a status string. Otherwise you'll get a message that does not help at all: "Exception TypeError: "'NoneType' object is not iterable" in 'liblo._callback' ignored"
    }

def quitty():
    ourNsmClient.sendStatusMessage("Preparing to quit. Wait for progress to finish")
    # Fake quit process
    ourNsmClient.updateProgress(0.1)
    sleep(0.5)
    ourNsmClient.updateProgress(0.5)
    sleep(0.5)
    ourNsmClient.updateProgress(0.9)
    ourNsmClient.updateProgress(1.0)
    return True

optionalFunctions = {
        "function_quit" : quitty,   # Accept zero parameters. Return True or False
        "function_showGui" : None,  # Accept zero parameters. Return True or False
        "function_hideGui" : None,  # Accept zero parameters. Return True or False
        "function_sessionIsLoaded" : None,  # No return value needed.
        }

ourNsmClient, process = nsmclient.init(prettyName = "ChronoTrigger", capabilities = capabilities, requiredFunctions = requiredFunctions, optionalFunctions = optionalFunctions,  sleepValueMs = 100)
# Direct send only functions for your program.
# ourNsmClient.updateProgress(value from 0.1 to 1.0) #give percentage during load, save and other heavy operations
# ourNsmClient.setDirty(True or False) #Inform NSM of the save status. Are there unsaved changes?

while True:
    process()


nsmclient.init(prettyName = "ChronoTrigger", capabilities = capabilities, )

# [[[[[ NSM CLIENT SECTION ]]]]] -------------------------------------


# Connect to JACK server
client = jack.Client("chronotrigger")
client.activate()

# Go to the beginning of the song
jack.Client.transport_locate(client, 1)
bar = 1

print("=) =) =) Current song position: Bar ", bar)
print("=) =) =) Song ends at bar ", endbar)
print("=) =) =) Switching to next song '", nextsong, "' in ", (endbar - bar), "bars")

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
