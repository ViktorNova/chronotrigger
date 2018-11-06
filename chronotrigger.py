#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
# TODO: Don't import JACK unless we're using JACK transport
import jack                 # Local copy from latest git master: https://raw.githubusercontent.com/spatialaudio/jackclient-python/master/jack.py
import configparser
from time import sleep
import subprocess
import os                   # TODO: Import only the parts of OS we actually need
import liblo



# nsm only
from nsmclient import NSMClient     # will raise an error and exit if this example is not run from NSM.

########################################################################
# General
########################################################################
niceTitle = "chronotrigger2"            # This is the name of your program. This will display in NSM and can be used in your save file

# Global variable declarations
songConfigFile      = None
bar                 = None
endbar              = None
nextsong            = None
transportProtocol   = None
host                = None
inport              = None
outport             = None
play                = None
playValue           = None
stop                = None
stopValue           = None
rewind              = None
rewindValue         = None
songPosition        = None

####################################################### This is a dirty hack and redundant. DO it the right way##################
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
    global transportProtocol
    global host
    global inport
    global outport
    global play
    global playValue
    global stop
    global stopValue
    global rewind
    global rewindValue
    global songPosition


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
    setlistConfig = configparser.ConfigParser(allow_no_value=True)
    songConfig.sections()
    # TODO: This next line is not ideal for Mac OS. Do an OS check and use ~/Library/Preferences/ if OSX
    setlistConfigFile = (os.environ.get('HOME') + '/.config/SETLIST.conf')
    if not os.path.isfile(setlistConfigFile):
        # TODO: List the NSM directory and output it in a comma separated list to pre-populate the setlist file
        print('Config file not found. Generating a new one at ', setlistConfigFile)
        setlistConfig.add_section('ACTIVE')
        setlistConfig.add_section('INACTIVE')
        setlistConfig.set('INACTIVE', '# You can use the inactive section to store multiple setlists if you want.')
        setlistConfig.add_section('ENGINE')
        setlistConfig.set('ENGINE', '# Transport can be either osc or jack')
        setlistConfig.set('ENGINE', 'transport', 'jack')
        setlistConfig.add_section('OSC')
        setlistConfig.set('OSC', '# Define your custom OSC parameters here')
        setlistConfig.set('OSC', 'host', 'localhost')
        setlistConfig.set('OSC', 'inport', '9000')
        setlistConfig.set('OSC', 'outport', '8000')
        setlistConfig.set('OSC', 'play', '/play')
        setlistConfig.set('OSC', 'playValue', '1')
        setlistConfig.set('OSC', 'stop', '/stop')
        setlistConfig.set('OSC', 'stopValue', '1')
        setlistConfig.set('OSC', 'rewind', '/time')
        setlistConfig.set('OSC', 'rewindValue', '0')
        setlistConfig.set('OSC', 'songPosition', '/beat/str')

        # TODO: Query /nsm/server/list and save its responses as a list. Then write that into the config file

        with open(setlistConfigFile, 'w') as newSetlistConfig:
            print("No global config file found. Creating one at ", setlistConfigFile)
            setlistConfig.write(newSetlistConfig)
            # TODO: Launch the GUI to allow configuration
            # showGui()
    else:
        print("OPEN:  Opening:", setlistConfigFile)
    # Open global config file
    setlistConfig.read(setlistConfigFile)
    print()

    # Read active setlist from config file, split it into a comma-delimited python list, and store that as 'setlist'
    try:
        setlist = setlistConfig['ACTIVE']['setlist'].split(",")
    except KeyError:
        print("No set list defined. Generating temporary one (FIX ME) in alphebetical order")
        setlist = [sessionName]  # FIXME
    print("SETLIST: ", setlist)
    # Figure out what position in the setlist we are currently on
    songNumber = setlist.index(sessionName)
    print("Current position in setlist: ", songNumber, " of ", len(setlist))
    try:
        nextsong = setlist[(songNumber + 1)]
    except IndexError:
        print("This is the last song of the set.")
        nextsong = None
    transportProtocol = setlistConfig['ENGINE']['transport']

    if transportProtocol == "jack":
        print("Using JACK transport")
    elif transportProtocol == "osc":
        print("Using OSC transport")
        host = setlistConfig['OSC']['host']
        inport = setlistConfig['OSC']['inport']
        outport = setlistConfig['OSC']['outport']
        play = setlistConfig['OSC']['play']
        playValue = setlistConfig['OSC']['playValue']
        stop = setlistConfig['OSC']['stop']
        stopValue = setlistConfig['OSC']['stopValue']

        rewind = setlistConfig['OSC']['rewind']
        rewindValue = setlistConfig['OSC']['rewindValue']
        songPosition = setlistConfig['OSC']['songPosition']
        # These print statements can probably be removed in the future:
        print("OSC host: ", host)
        print("OSC in port: ", inport)
        print("OSC out port: ", outport)
        print("OSC out port: ", outport)
        print("Play message: ", play)
        print("Play value: ", playValue)
        print("Stop message: ", stop)
        print("Stop value: ", stopValue)
        print("Rewind message: ", rewind)
        print("Rewind value: ", rewindValue)
        print("Song position message: ", songPosition)
    else:
        sys.exit("Invalid transport protocol. Please fix your config.")

    print("NEXT SONG: ", nextsong)

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

    if transportProtocol is "jack":
        print("Disconnecting from JACK")
        client.deactivate()
        client.close()

    if nextsong is None:
        print("Set list is over. No next song to switch to.")
        return True

    if bar >= endbar:
        switch_to_next_song()
    return True
    # Exit is done by NSM kill.


def switch_to_next_song():
    print("Closing session and loading next song '", nextsong, "' NOW!")
    message = liblo.Message("/nsm/server/open", nextsong)
    print(message)
    liblo.send(NSM_URL, message)


def showGUICallback():
    # Put your code that shows your GUI in here
    print("Showing GUI...")

    # TODO: Open a dedicated GUI to edit the endbar
    # TODO: Make the GUI validate 'endbar', the value has to be 1 or greater, or this will finish instantly
    gui_process = subprocess.Popen(["xdg-open", str(songConfigFile)])
                                   # stdout=subprocess.PIPE,
                                   # preexec_fn=os.setsid)

    # nsmClient.announceSaveStatus(False) # Announce your save status (dirty = False / clean = True)
    # nsmClient.announceGuiVisibility(isVisible=True)  # Inform NSM that the GUI is now visible. Put this at the end.


def hideGUICallback():
    # Put your code that hides your GUI in here
    print("Hiding GUI not implemented yet, you have to save and close the text editor yourself.")

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
# Start main program loop.
########################################################################

# showGUICallback()  # If you want your GUI to be shown by default, uncomment this line
print("Let's go!")

# TODO: Get this to be able to send OSC messages to NSM.
# The next line is a failed attempt, but it should be sort of related

# message = liblo.Message("/nsm/server/open", nextsong)

NSM_URL = 'osc.udp://' + str(nsmClient.nsmOSCUrl[0]) + ':' + str(nsmClient.nsmOSCUrl[1])  + '/'
print(NSM_URL)

# THIS IS WHERE THE ACTUAL FUNCTIONAL CODE OF THE PROGRAM RUNS! ----------------------

# Give clients a chance to load
# TODO: Query nsmd to get all_clients_are_loaded = True instead (if running under NSM)
sleep(1)


# START THE TRANSPORT ----------------------------------
print("STARTING TRANSPORT...")


def startJackTransport():
    # Connect to JACK server
    global endbar
    jack.Client.transport_locate(client, 1)
    print("________________________________________________")
    print("Transport state is: ", client.transport_state)
    print("=) Song ends at bar ", endbar)
    print("=) Switching to next song '", nextsong, "' in ", (endbar - 1), "bars")
    jack.Client.transport_start(client)

def rewindOSCTransport(url):
    # Rewind to beginning of song
    message = liblo.Message(str(rewind), str(rewindValue))
    print("Sending ", rewind, rewindValue, " to ", url)
    liblo.send(url, message)


def startOSCTransport(url):
    # Stop playback in case it is currently playing
    message = liblo.Message(str(stop), str(stopValue))
    print("Sending ", stop, stopValue, " to ", url)
    liblo.send(url, message)
    # Begin playback
    message = liblo.Message(str(play), str(playValue))
    print("Sending ", play, playValue, " to ", url)
    liblo.send(url, message)


bar = 0

# Create JACK client or OSC Server
if transportProtocol is "jack":
    print("\nSTART: Connecting to JACK server")
    client = jack.Client(nsmClient.ourClientNameUnderNSM)
    client.activate()
    print("START: Connected to JACK as:" + client.name)
    # Go to the beginning of the song
    startJackTransport()
else:
    print("Creating OSC server")
    server = liblo.Server(inport)
    endbar = float(endbar)  # Convert endbar to a float to handle Reaper's
    OSC_URL = 'osc.udp://' + str(host) + ':' + str(outport) + '/'

    # WAIT FOR CONFIRMATION THAT REAPER IS UP AND RUNNING AND THE SESSION IS LOADED
    # Reaper sends /play when initializing a newly opened project (among other things),
    # but also when playback begins. This is important because in the rare case that Reaper
    # opens before this, clicking play manually in Reaper will unblock this step and allow us to continue
    # TODO: Find a better way to do this. I could try pinging Reaper with messages that get a response until it responds - for instance I could alternate /pause and /stop forever until Reaper responds back with a /pause or /stop. Maybe I'm overthinking it
    reaperIsReady = False
    while not reaperIsReady:
            server.recv(400)    # Receive OSC messages every 400ms

            def reaperPing(path, args):
                global reaperIsReady
                reaperIsReady = True
                print("Received /play message from Reaper. "
                      "The session is loaded (or playback was started manually)")

            server.add_method("/play", None, reaperPing)

    rewindOSCTransport(OSC_URL)
    startOSCTransport(OSC_URL)

print("Entering main loop")
try:
    while bar < endbar:     # Wait for the song to end
        nsmClient.reactToMessage()  # Make sure this exists somewhere in your main loop

        if transportProtocol is "jack":
            transport = client.transport_query()
            try:
                bar = transport[1]['bar']
            except KeyError:
                print("Waiting for sequencer to start.. \n")
            # THIS SECTION IS FOR DEBUGGING.
            # It should probably be commented out since this is not generally run in the terminal.
            # TODO: show this stuff in the GUI when it exists.
            print("Full JACK Transport Status: ", transport, "\n")
            print("Transport state is: ", client.transport_state)
            print("Current song position: Bar ", bar, "               ")
            print("Song ends at bar ", endbar, "                      ")
            print("Switching to next song '", nextsong, "' in ", (endbar - bar), "bars \n")
            # Only react to events once per second - this keeps this from consuming lots of CPU
            sleep(1) # TODO: instead of sleeping 1 second here, do it on the beat. Could be easily done with some BPM math

        else:
            server.recv(400)    # Receive OSC messages every 400ms

            def receiveReaperCurrentBar(path, args):
                print("received message '%s'" % path, args)
                s = args[0].rsplit(".",1)
                print("s = ", s)
                global bar          # access bar from the global scope
                bar = float(s[0])   # convert Reaper's time beat position into a float, drop the last decimal

            server.add_method("/beat/str", None, receiveReaperCurrentBar)

            print("Bar = ", bar)


except TypeError:
    print("Cannot determine song position. Stopping...")
    exit(1)

# print("SONG IS OVER!")
# print("Pretending to switch to the next song now (please delete this section)")
# exit(0)

# We have now reached the end of the song, so time to call the exit function
# which will clean up nicely, then switch to the next song
exitProgram(nsmClient.ourPath,nsmClient.ourClientNameUnderNSM,nsmClient.sessionName)


