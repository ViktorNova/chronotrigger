#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import jack                 # Local copy from latest git master: https://raw.githubusercontent.com/spatialaudio/jackclient-python/master/jack.py
import configparser
from time import sleep
import subprocess
import os                   # TODO: Import only the parts of OS we actually need

# nsm only
from nsmclient import NSMClient     # will raise an error and exit if this example is not run from NSM.

########################################################################
# General
########################################################################
niceTitle = "chronotrigger2"            # This is the name of your program. This will display in NSM and can be used in your save file

# Global variable declarations
configFile      = None
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
    global configFile
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
    config = configparser.ConfigParser()
    config.sections()
    configFile = (ourPath + "/chronotrigger.conf")
    if not os.path.isfile(configFile): # TODO: Change this to a try/except
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
    # return True, "chronotrigger.conf" # This was from the old way




def exitProgram(ourPath, sessionName, ourClientNameUnderNSM):
    """This function is a callback for NSM.
    We have a chance to close our clients and open connections here.
    If not nsmclient will just kill us no matter what
    """
    print("exitProgram");
    # Exit is done by NSM kill.


def showGUICallback():
    # Put your code that shows your GUI in here
    try:
        configFile
    except NameError:
        print("Not showing the GUI yet")
    else:
        print("Showing GUI...")
        gui_process = subprocess.Popen(["xdg-open", str(configFile)],
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

while True:
    nsmClient.reactToMessage()  # Make sure this exists somewhere in your main loop
    # nsmClient.announceSaveStatus(False) # Announce your save status (dirty = False / clean = True)
    sleep(0.05)
