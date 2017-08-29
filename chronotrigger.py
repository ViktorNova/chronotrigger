#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import jack                 # Local copy from latest git master: https://raw.githubusercontent.com/spatialaudio/jackclient-python/master/jack.py
import configparser
from time import sleep
import subprocess
import os                   # TODO: Import only the parts of OS we actually need
import liblo                # This is a dirty hack and redundant. DO it the right way



# nsm only
from nsmclient import NSMClient     # will raise an error and exit if this example is not run from NSM.

########################################################################
# General
########################################################################
niceTitle = "chronotrigger2"            # This is the name of your program. This will display in NSM and can be used in your save file

# Global variable declarations
songConfigFile      = None
bar             = None
endbar          = None
nextsong        = None

# Global variable declarations
session_name    = None
songConfigFile      = None
bar             = None
endbar          = None
nextsong        = None

########################################################################
# Prepare the NSM Client
# This has to be done as the first thing because NSM needs to get the paths
# and may quit if NSM environment var was not found.
#
# This is also where to set up your functions that react to messages from NSM,
########################################################################
# Here are some variables you can use:
# ourPath               = Full path to your NSM save file/directory with serialized NSM extension
# ourClientNameUnderNSM = Your NSM save file/directory with serialized NSM extension and no path information
# sessionName           = The name of your session with no path information
########################################################################


def saveCallback(ourPath, sessionName, ourClientNameUnderNSM):
    # TODO: Send this to the NSM server
    message = ("/nsm/client/message", "i:0 s:NSM save commands are ignored. You must open the GUI to save changes")
    print(message)


def openCallback(ourPath, sessionName, ourClientNameUnderNSM):
    # Make sure we're setting these global variables
    global songConfigFile
    global endbar
    global nextsong

    # TODO: If config file is invalid or list a non existant session,
    # TODO: report an error message to nsmd & show GUI (can I do both without a subprocess?)
    # TODO: Get rid of some of this printy crap
    sessionpath = os.path.split(ourPath)[0]   # Strips out the serialized directory name since we can only have one instance
    print()
    print("LOAD:  Session Name: ", sessionName)
    print("LOAD:  Client ID = ", ourClientNameUnderNSM)
    print("LOAD:  ourPath = ", ourPath)
    print("LOAD:  sessionpath is = ", sessionpath)
    ourPath = sessionpath
    print()

    # READ THIS SONG'S CONFIG FILE
    songConfig = configparser.ConfigParser()
    songConfig.sections()
    songConfigFile = (ourPath + "/chronotrigger.conf")
    if not os.path.isfile(songConfigFile): # TODO: Change this to a try/except
        print('Config file not found. Generating a new one at ', songConfigFile)
        songConfig.add_section('SONG')
        songConfig.set('SONG', 'endbar', '9999999')
        with open(songConfigFile, 'w') as newSongConfig:
            songConfig.write(newSongConfig)
            # TODO: Launch the GUI to allow configuration
            # showGui()
    else:
        print("OPEN:  Opening:", songConfigFile)
        songConfig.read(songConfigFile)

    endbar = int(songConfig['SONG']['endbar'])
    print("OPEN: endbar = ", endbar)
    # TODO: Uncomment this once I make a better NSM client that can show this message to the user
    # infoMessage = liblo.Message("/nsm/client/message", "i:0 s:" + str(endbar))
    # liblo.send(NSM_URL, infoMessage)

    # READ GLOBAL SETLIST CONFIG FILE
    setlistConfig = configparser.ConfigParser()
    songConfig.sections()
    # TODO: Using XDG_CONFIG_HOME probably breaks this on Mac OS. Do an OS check and use ~/Library/Preferences/ if OSX
    setlistConfigFile = (os.getenv('XDG_CONFIG_HOME') + "/SETLIST.conf")
    if not os.path.isfile(setlistConfigFile): # confTODO: Create a default config so we can't get errors
        print('Config file not found. Generating a new one at ', setlistConfigFile)
        setlistConfig.add_section('ACTIVE')
        setlistConfig.add_section('INACTIVE')
        setlistConfig.set('INACTIVE', 'Note', 'You can use the inactive section to store multiple setlists if you want. Everything not in the [ACTIVE] section will be ignored')

        # TODO: Query /nsm/server/list and save its responses as a list. Then write that into the config file

        with open(setlistConfigFile, 'w') as newSetlistConfig:
            setlistConfig.write(newSetlistConfig)
            # TODO: Launch the GUI to allow configuration
            # showGui()
    else:
        print("OPEN:  Opening:", setlistConfigFile)
    # Open global config file
    setlistConfig.read(setlistConfigFile)
    print()

    # Read active setlist from config file, split it into a comma-delimited python list, and store that as 'setlist'
    setlist = setlistConfig['ACTIVE']['setlist'].split(",")

    print("SETLIST: ", setlist)
    # Figure out what position in the setlist we are currently on
    songNumber = setlist.index(sessionName)
    print("Current position in setlist: ", songNumber)

    # TODO: Add an exception if there is no next song. That way this won't crash
    nextsong = setlist[(songNumber + 1)]

    # TODO
    print("NEXT SONG: ", nextsong)

    # nextsong = config['SONG']['nextsong']
    # return True, "chronotrigger.conf" # This was from the old way


def exitProgram(ourPath, sessionName, ourClientNameUnderNSM):
    """This function is a callback for NSM.
    We have a chance to close our clients and open connections here.
    If not nsmclient will just kill us no matter what
    """
    print("\nexitProgram has been called. \n");
    # Clean up and exit because the song is now over. TODO: Make this trigger on KILL and HUP as well
    # ourNsmClient.updateProgress(0.1)
    # TODO: See if nsmclient2 can send messages to the server to announce in the GUI.. this is probably not important at all
    # ourNsmClient.sendStatusMessage("Preparing to quit. Wait for progress to finish")
    print("Song is over.")
    print("Disconnecting from JACK")
    client.deactivate()
    # ourNsmClient.updateProgress(0.5)
    client.close()
    # ourNsmClient.updateProgress(0.7)
    if bar >= endbar:
        switch_to_next_song()
    # ourNsmClient.updateProgress(1.0)
    return True
    # Exit is done by NSM kill.


def switch_to_next_song():
    print("Closing session and loading next song '", nextsong, "' NOW!")
    message = liblo.Message("/nsm/server/open", nextsong)
    print(message)
    liblo.send(NSM_URL, message)


def showGUICallback():
    # Put your code that shows your GUI in here
    try:
        songConfigFile
    except NameError:
        print("Not showing the GUI yet")
    else:
        print("Showing GUI...")
        gui_process = subprocess.Popen(["xdg-open", str(songConfigFile)],
                                       stdout=subprocess.PIPE,
                                       preexec_fn=os.setsid)
    nsmClient.announceGuiVisibility(isVisible=True)  # Inform NSM that the GUI is now visible. Put this at the end.


def hideGUICallback():
    # Put your code that hides your GUI in here
    print("hideGUICallback");
    print("TODO: fix this proper")
    nsmClient.announceGuiVisibility(isVisible=False)  # Inform NSM that the GUI is now hidden. Put this at the end.


nsmClient = NSMClient(prettyName = niceTitle,
                      saveCallback = saveCallback,
                      openOrNewCallback = openCallback,
                      showGUICallback = showGUICallback,  # Comment this line out if your program does not have an optional GUI
                      hideGUICallback = hideGUICallback,  # Comment this line out if your program does not have an optional GUI
                      supportsSaveStatus = False,         # Change this to True if your program announces it's save status to NSM
                      exitProgramCallback = exitProgram,
                      loggingLevel = "info", # "info" for development or debugging, "error" for production. default is error.
                      )

# If NSM did not start up properly the program quits here.

########################################################################
# If your project uses JACK, activate your client here
# You can use jackClientName or create your own
########################################################################
jackClientName = nsmClient.ourClientNameUnderNSM

########################################################################
# Start main program loop.
########################################################################

# showGUICallback()  # If you want your GUI to be shown by default, uncomment this line
print("Entering main loop")

# TODO: Get this to be able to send OSC messages to NSM.
# The next line is a failed attempt, but it should be sort of related

# message = liblo.Message("/nsm/server/open", nextsong)

NSM_URL = 'osc.udp://' + str(nsmClient.nsmOSCUrl[0]) + ':' + str(nsmClient.nsmOSCUrl[1])  + '/'
print(NSM_URL)

# THIS IS WHERE THE ACTUAL FUNCTIONAL CODE OF THE PROGRAM RUNS! ----------------------
print("\nSTART: Connecting to JACK server")
sleep(2) # TODO: take these sleeps out once more precautions are in place
# Connect to JACK server
client = jack.Client(nsmClient.ourClientNameUnderNSM)
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
    # TODO: instead of sleeping 1 second here, do it on the beat. Could be easily done with some BPM math
    sleep(1)
    transport = client.transport_query()
    # TODO: change this to try, wait for sequencer to start instead of failing right here if "bar" does not exist yet
    bar = transport[1]['bar']

    # THIS SECTION IS FOR DEBUGGING.
    # It should be commented out since this is not generally run in the terminal.
    # TODO: show this stuff in the GUI when it exists.
    print("Full JACK Transport Status: ", transport, "\n")

    print("Transport state is: ", client.transport_state)
    print("Current song position: Bar ", bar, "               ")
    print("Song ends at bar ", endbar, "                      ")
    print("Switching to next song '", nextsong, "' in ", (endbar - bar), "bars \n")

# We have now reached the end of the song, so time to call the exit function
# which will clean up nicely, then switch to the next song
exitProgram(nsmClient.ourPath,nsmClient.ourClientNameUnderNSM,nsmClient.sessionName)

while True:
    # nsmClient.announceSaveStatus(False) # Announce your save status (dirty = False / clean = True)
    nsmClient.reactToMessage()  # Make sure this exists somewhere in your main loop
    sleep(0.05)
