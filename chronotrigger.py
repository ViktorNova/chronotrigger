#!/usr/bin/env python3
# Switch to the next song in NSM when Jack transport reaches a certain point
# __author__ = 'Viktor Nova'
# from _ast import arg
from _ast import excepthandler
# from sys import stdout

import os

# for debuging - uncomment the os.environ line
# and change the value to your current NSM url.
# This changes each time nsmd is launched, you
# can find it out by adding xterm to your session,
# then running "echo $NSM_URL"

import sys
# The following line is for testing. Uncomment and change to the address of your nsmd server for testing
# os.environ["NSM_URL"] = "osc.udp://localhost:17274/"


NSM_URL = os.getenv('NSM_URL')
if not NSM_URL:
    print("NSM_URL is not set, not running inside Non Session Manager, exiting")
    sys.exit()
print("NSM Daemon found at ", NSM_URL)

# TODO: Make this work outside NSM with arguments and an arbitrary OSC message/receiver
# import argparse
# parser = argparse.ArgumentParser()
# parser.add_argument("endbar")   # First argument (# Bar where song ends. When JACK transport reaches this bar, the song is considered to be over, and we will switch sessions and load the next song)
# parser.add_argument("nextsong") # Second argument  (Name of the song we will automatically switch to when this song is finished)
# args = parser.parse_args()

import liblo
import nsmclient1Deprecated as nsmclient           # Local copy from latest git master: https://raw.githubusercontent.com/nilsgey/pynsmclient/master/nsmclient.py
import jack                 # Local copy from latest git master: https://raw.githubusercontent.com/spatialaudio/jackclient-python/master/jack.py
import configparser
from time import sleep
import subprocess

# Global variable declarations
session_name    = None
configFile      = None
bar             = None
endbar          = None
nextsong        = None

# NSM client capabilities
capabilities = {
    "switch" : False,		    # client is capable of responding to multiple `open` messages without restarting
    "dirty" : False, 		    # client knows when it has unsaved changes
    "progress" : True,		    # client can send progress updates during time-consuming operations
    "message" : True, 		    # client can send textual status updates
    "optional-gui" : True,      # client has an optional GUI
    "server-control" : True     # client can control the NSM server
    }

# Load client & parse config file
def myLoadFunction(pathBeginning, clientId):
    # Make sure we're setting these global variables
    global session_name
    global configFile
    global endbar
    global nextsong

    # TODO: If config file doesn't exist, create one
    # TODO: If config file is invalid or list a non existant session,
    # TODO: report an error message to nsmd & show GUI (can I do both without a subprocess?)
    # TODO: Get rid of some of this crap
    sessionpath = os.path.split(pathBeginning)[0]   # Strips out the serialized directory name since we can only have one instance
    session_name = nsmclient.states.prettyNSMName
    print()
    print("LOAD:  Session Name: ", nsmclient.states.prettyNSMName)
    print("LOAD:  Client ID = ", nsmclient.states.clientId)
    print("LOAD:  pathBeginning = ", pathBeginning)
    print("LOAD:  sessionpath is = ", sessionpath)
    pathBeginning = sessionpath
    print()

    # READ THIS SONG'S CONFIG FILE
    config = configparser.ConfigParser()
    config.sections()
    configFile = (pathBeginning + "/chronotrigger.conf")
    if not os.path.isfile(configFile): # TODO: Create a default config so we can't get errors
        print('Config file not found. Generating a new one at ', configFile)
        config.add_section('SONG')
        config.set('SONG', 'endbar', '9999999')
        with open(configFile, 'w') as newConfig:
            config.write(newConfig)
            # TODO: Launch the GUI to allow configuration
            # showGui()
    else:
        print("OPEN:  Opening:", configFile)
        config.read(configFile)

    endbar = int(config['SONG']['endbar'])
    print("OPEN: endbar = ", endbar)
    # TODO: Uncomment this once I make a better NSM client that can show this message to the user
    # infoMessage = liblo.Message("/nsm/client/message", "i:0 s:" + str(endbar))
    # liblo.send(NSM_URL, infoMessage)

    # READ GLOBAL SETLIST CONFIG FILE
    # TODO: Using XDG_CONFIG_HOME probably breaks this on Mac OS. Do an OS check and use ~/Library/Preferences/ if OSX
    setlistConfigFile = (os.getenv('XDG_CONFIG_HOME') + "/SETLIST.conf")
    if not os.path.isfile(setlistConfigFile): # TODO: Create a default config so we can't get errors
        print('Config file not found. Generating a new one at ', setlistConfigFile)
        config.add_section('ACTIVE')
        config.add_section('INACTIVE')
        config.set('INACTIVE', 'Note', 'You can use the inactive section to store multiple setlists if you want. Everything not in the [ACTIVE] section will be ignored')

        # TODO: Query /nsm/server/list and save its responses as a list. Then write that into the config file

        with open(setlistConfigFile, 'w') as newConfig:
            config.write(newConfig)
            # TODO: Launch the GUI to allow configuration
            # showGui()
    else:
        print("OPEN:  Opening:", configFile)
        config.read(configFile)

    # nextsong = config['SONG']['nextsong']



    return True, "chronotrigger.conf"

def mySaveFunction():
    # TODO: This never gets called when you click save, for some reason. Not the end of the world for now
    message = liblo.Message("/nsm/client/message", "i:0 s:You must open the GUI to save changes")
    print(message)
    liblo.send(NSM_URL, message)

requiredFunctions = {
    "function_open" : myLoadFunction,  # Accept two parameters. Return two values. A bool and a status string. Otherwise you'll get a message that does not help at all: "Exception TypeError: "'NoneType' object is not iterable" in 'liblo._callback' ignored"
    "function_save" : mySaveFunction,  # Accept one parameter. Return two values. A bool and a status string. Otherwise you'll get a message that does not help at all: "Exception TypeError: "'NoneType' object is not iterable" in 'liblo._callback' ignored"
    }

def showGui():
    try:
        configFile
    except NameError:
        print("Not showing the GUI yet")
    else:
        print("Showing GUI...")
        gui_process = subprocess.Popen(["xdg-open", str(configFile)],
            stdout=subprocess.PIPE,
            preexec_fn=os.setsid)


def quitty():
    ourNsmClient.updateProgress(0.1)
    ourNsmClient.sendStatusMessage("Preparing to quit. Wait for progress to finish")
    print()
    print("Song is over.")
    print("Disconnecting from JACK")
    client.deactivate()
    ourNsmClient.updateProgress(0.5)
    client.close()
    ourNsmClient.updateProgress(0.7)
    if bar >= endbar:
        switch_to_next_song()
    ourNsmClient.updateProgress(1.0)
    return True

def switch_to_next_song():
    print("Closing session and loading next song '", nextsong, "' NOW!")
    message = liblo.Message("/nsm/server/open", nextsong)
    print(message)
    liblo.send(NSM_URL, message)

# These section define what functions get called when the corresponding event happens
optionalFunctions = {
        "function_quit" : quitty,         # Accept zero parameters. Return True or False
        "function_showGui" : showGui,     # Accept zero parameters. Return True or False
        "function_hideGui" : None,          # Accept zero parameters. Return True or False
        "function_sessionIsLoaded" : None,  # No return value needed.
        }


# [[[[[ START PROGRAM ]]]]] -------------------------------------
ourNsmClient, process = nsmclient.init(prettyName = "ChronoTrigger", capabilities = capabilities, requiredFunctions = requiredFunctions, optionalFunctions = optionalFunctions,  sleepValueMs = 100)
# Direct send only functions for your program.
# ourNsmClient.updateProgress(value from 0.1 to 1.0) #give percentage during load, save and other heavy operations
# ourNsmClient.setDirty(True or False) #Inform NSM of the save status. Are there unsaved changes?
process()


# THIS IS WHERE THE ACTUAL FUNCTIONAL CODE OF THE PROGRAM RUNS! ----------------------
print("\nSTART: Connecting to JACK server")
sleep(2)
# Connect to JACK server
client = jack.Client(nsmclient.states.clientId)
client.activate()
print("START: Connected to JACK as:" + client.name)

# Go to the beginning of the song
bar = 1
jack.Client.transport_locate(client, bar)
print("________________________________________________")
print("Transport state is: ", client.transport_state)
print("=) Current song position: Bar ", bar)
print("=) Song ends at bar ", endbar)
print("=) Switching to next song '", nextsong, "' in ", (endbar - bar), "bars")

# Give clients a chance to load
# TODO: Query nsmd to get all_clients_are_loaded = True instead (if running under NSM)
sleep(1)


# Start the transport
print("STARTING TRANSPORT...")
jack.Client.transport_start(client)
print("\033[F" + "                      " + "\033[F") # Clear out that last line
    # Wait for the song to end
while bar < endbar:
    # Sleep for a second to allow the sequencer to start
    # TODO: wait for sequencer to start instead of failing right here if "bar" does not exist yet
    sleep(1)
    transport = client.transport_query()
    bar = transport[1]['bar']

    # THIS SECTION IS FOR DEBUGGING.
    # It should be commented out since this is not generally run in the terminal.
    # TODO: show this stuff in the GUI when it exists.
    print("Full JACK Transport Status: ", transport)

    # status = client.transport_state
    # print("\033[F" + "\033[F" + "\033[F" + "\033[F" + "\033[F") # Go 4 lines up. (This is a dumb way to do it and doesn't work in all terminals)
    # print("Transport state is: ", status)
    # print("Current song position: Bar ", bar, "               ")
    # print("Song ends at bar ", endbar, "                      ")
    # print("Switching to next song '", nextsong, "' in ", (endbar - bar), "bars           ")



# Clean up and exit because the song is now over. TODO: Make this trigger on KILL and HUP as well
quitty()


def switch_to_next_song():
    print("Closing session and loading next song '", nextsong, "' NOW!")
    message = liblo.Message("/nsm/server/open", nextsong)
    print(message)
    liblo.send(NSM_URL, message)
