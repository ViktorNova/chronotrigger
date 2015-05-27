# -*- coding: utf-8 -*-

"""
Author: Nils Gey ich@nilsgey.de http://www.nilsgey.de  April 2013.
Non Session Manager Author: Jonathan Moore Liles  <male@tuxfamily.org> http://non.tuxfamily.org/nsm/

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


"""Usage: Import this file from your python application with
import nsmclient
and then call init() with the right parameters.

See example.py
"""

#You need pyliblo for Python3 for nsmclient and of course an installed and running non-session-manager
import liblo, os
from signal import signal, SIGTERM, SIGKILL
import __main__

#We can change the pretty name as only command line option though. Enabling multiple instances of the same. But it must be a fixed name. It will tell NSM which instance/saved file to load.
NSM_ANNOUNCE = "/nsm/server/announce"
API_VERSION_MAJOR = 1
API_VERSION_MINOR = 2

class States(object):
    def __init__(self, env):
        self.sessionIsLoaded = False #NSM reported the session is loaded
        self.nsmUrl = env # NSM_URL environment variable
        self.welcomeMessage = self.sessionManagerName = None #set by ourNsmClient.welcome()
        self.nsmCapabilities = set() #set by ourNsmClient.welcome(). You can test it with "if capability in self.nsmCapabilities:"
        self.pathBeginning =  self.prettyNSMName = self.clientId = None # set by ourNsmClient.openFile()
        self.lastDirtyState = False #Everything is clean and shiny in the beginning.

class OurNsmClient(object):
    def __init__(self, states):
        #Functions to re-implement
        #Obligatory functios
        self.function_open = self.nothing
        self.function_save = self.nothing

        #Optional functions
        self.function_quit = self.nothing
        self.function_showGui = self.nothing
        self.function_hideGui = self.nothing
        self.function_sessionIsLoaded = self.nothing

        #Add functions to our osc server that receives from NSM.
        signal(SIGTERM, self._signal_handler) #NSM sends SIGTERM. Nothing more.
        self.libloServer = liblo.Server() #I hope that is a random, free, port
        self.libloServer.add_method("/reply", None, self.welcome) # NSM Welcome Message
        self.libloServer.add_method("/error", None, self.receiveError) # NSM Error messages
        self.libloServer.add_method("/nsm/client/open", None, self.openFile)
        self.libloServer.add_method("/nsm/client/save", None, self.saveFile)
        self.libloServer.add_method("/nsm/client/session_is_loaded", None, self.isLoaded)
        self.libloServer.add_method("/nsm/client/show_optional_gui", None, self.showGui)
        self.libloServer.add_method("/nsm/client/hide_optional_gui", None, self.hideGui)

        #For your information. There are function which can just be called directly:
        #ourNsmClient.updateProgress(value from 0.1 to 1.0) #give percentage during load, save and other heavy operations
        #ourNsmClient.setDirty(True or False) #Inform NSM of the save status. Are there unsaved changes?
        #ourNsmClient.sendError(errorCode or String, message string)

        self.errorCodes = {"ERR_GENERAL":   -1,
                        "ERR_INCOMPATIBLE_API" : -2,
                        "ERR_BLACKLISTED" : -3,
                        "ERR_LAUNCH_FAILED" : -4,
                        "ERR_NO_SUCH_FILE" : -5,
                        "ERR_NO_SESSION_OPEN" : -6,
                        "ERR_UNSAVED_CHANGES" : -7,
                        "ERR_NOT_NOW" : -8,
                        "ERR_BAD_PROJECT" : -9,
                        "ERR_CREATE_FAILED" : -10,
                        -1: -1,
                        -2: -2,
                        -3: -3,
                        -4: -4,
                        -5: -5,
                        -6: -6,
                        -7: -7,
                        -8: -8,
                        -9: -8,
                        -10: -10,
                        -11: -11,
                        }

        self.libloServer.add_method(None, None, self.fallback) # register a fallback for unhandled messages
        self.states = states #A shortcut to the global states


    def nothing(*args):
        return True, "Fine"

    def welcome(self, path, argList, types):
        """/reply "/nsm/server/announce" s:message s:name_of_session_manager s:capabilities

        Receiving this message means we are now part of a session"""
        #print ("Welcome", path, argList)
        #path is "/reply"
        try:
            devNull, self.states.welcomeMessage, self.states.sessionManagerName, self.states.nsmCapabilities = argList
        except:
            print ("Unknown /reply:", path, argList)

        if self.states.nsmCapabilities:
            self.states.nsmCapabilities = set(self.states.nsmCapabilities[1:-1].split(":"))

    def openFile(self, path, argList, types):
        #TODO: send real errors with error codes
        """/nsm/client/open s:path_to_instance_specific_project s:display_name s:client_id

        A response is REQUIRED as soon as the open operation has been
        completed. Ongoing progress may be indicated by sending messages
        to /nsm/client/progress.
        """

        self.states.pathBeginning, self.states.prettyNSMName, self.states.clientId = argList
        loadState, fileNameOrLoadMessage = self.function_open(self.states.pathBeginning, self.states.clientId) #Call the user function
        if loadState:
            liblo.send(states.nsmUrl, "/reply", "/nsm/client/open", " ".join([self.states.pathBeginning+"/"+fileNameOrLoadMessage, "successfully opened"]))
        else: #the string indicates the error.
            liblo.send(states.nsmUrl, "/error", "/nsm/client/open", -1, " ".join(["Not loaded. Error:", fileNameOrLoadMessage]))
            os.kill (os.getpid(), SIGKILL) #Somehow a SIGTERM here gets ignored.
            #this can go wrong if the quit-hook user function tries to shutdown things which have not been initialized yet. For example the jack engine which is by definition started AFTER nsm-open


    def saveFile(self, path, argList, types):
        #TODO: send real errors with error codes
        """/nsm/client/save

        This message will only be delivered after a previous open
        message, and may be sent any number of times within the course
        of a session (including zero, if the user aborts the session).

        argList is empty, types is empty.
        """
        saveState, fileNameOrSaveMessage = self.function_save(self.states.pathBeginning) #Call the user function
        if saveState:
            liblo.send(states.nsmUrl, "/reply", "/nsm/client/save", " ".join([self.states.pathBeginning+"/"+fileNameOrSaveMessage, "successfully saved"]))
            self.setDirty(False, internal=True)
        else: #the string indicates the error.
            print (" ".join(["Not saved. Error:", fileNameOrSaveMessage]))
            liblo.send(states.nsmUrl, "/error", "/nsm/client/save", -1, " ".join(["Not saved. Error:", fileNameOrSaveMessage]))

    def isLoaded(*args):
        """No parameters"""
        self.function_sessionIsLoaded()

    def updateProgress(self, progressValue):
        """/nsm/client/progress f:progress

        progressValue must be a number between 0 and 1

        For potentially time-consuming operations, such as save and
        open, progress updates may be indicated throughout the
        duration by sending a floating point value between 0.0 and
        1.0, 1.0 indicating completion, to the NSM server. The
        server will not send a response to these messages, but will
        relay the information to the user.
        """
        if "progress" in states.clientCapabilities:
            liblo.send(states.nsmUrl, "/nsm/client/progress", float(progressValue))
        else:
            print ("Warning. You tried to send a progress update but did not initialize your NSM client with the 'progress' capability. Message not sent. Get rid of this warning by setting the capability flag or remove the progress update")

    def setDirty(self, trueOrFalse, internal = False):
        """/nsm/client/progress f:progress

        /nsm/client/is_dirty
        /nsm/client/is_clean

        Some clients may be able to inform the server when they have
        unsaved changes pending. Such clients may optionally send
        is_dirty and is_clean messages. Clients which have this
        capability should include :dirty: in their announce
        capability string.
        """
        if "dirty" in states.clientCapabilities:
            if trueOrFalse and states.lastDirtyState is False:
                states.lastDirtyState = True
                liblo.send(states.nsmUrl, "/nsm/client/is_dirty")
            elif (not trueOrFalse) and states.lastDirtyState is True:
                states.lastDirtyState = False
                liblo.send(states.nsmUrl, "/nsm/client/is_clean")
            #else: #whatever it was, we were already at this state. Just ignore
            #    pass

        else:
            if not internal:
                print ("Warning. You tried to send a dirty/clean update but did not initialize your NSM client with the 'dirty' capability. Message not sent. Get rid of this warning by setting the capability flag to True or remove the dirty update")

    def sendStatusMessage(self, message, priority = 0):
        """/nsm/client/message i:priority s:message
        Clients may send miscellaneous status updates to the server
        for possible display to the user. This may simply be chatter
        that is normally written to the console. priority should be
        a number from 0 to 3, 3 being the most important. Clients
        which have this capability should include :message: in their
        announce capability string. """
        if "message" in states.clientCapabilities:
            liblo.send(states.nsmUrl, "/nsm/client/message", int(priority), str(message))
        else:
            print ("Warning. You tried to send a status message but did not initialize your NSM client with the 'message' capability. Message not sent. Get rid of this warning by setting the capability flag to True or remove the message update")

    def setLabel(self, label):
        """Set the label in the NSM gui"""
        liblo.send(states.nsmUrl, "/nsm/client/label", str(label))

    #GUI
    def showGui(self, *args):
        """Only execute if the server has the capabilities to handle
        optional GUIs. If not ignore that command"""
        if "optional-gui" in self.states.nsmCapabilities:
            self.function_showGui()
            liblo.send(states.nsmUrl, "/nsm/client/gui_is_shown")
        else:
            pass #TODO: send general error?

    def hideGui(self, *args):
        """Only execute if the server has the capabilities to handle
        optional GUIs. If not ignore that command"""
        if "optional-gui" in self.states.nsmCapabilities:
            self.function_hideGui()
            liblo.send(states.nsmUrl, "/nsm/client/gui_is_hidden")
        else:
            pass #TODO: send general error?

    #Error, Fallback and Quit functions.
    def receiveError(self, path, args, types):
        """/error "/nsm/server/announce" i:error_code s:error_message
        -1 ERR_GENERAL  General Error
        -2 ERR_INCOMPATIBLE_API Incompatible API version
        -3 ERR_BLACKLISTED  Client has been blacklisted.
        """
        devNull, errorCode, errorMessage = args
        if args[1] == -2: #ERR_INCOMPATIBLE_API
            #self.function_quit()
            self.sendError(-2, "Incompatible API. Client shuts down itself")
            os.kill (os.getpid(), SIGKILL) #Somehow a SIGTERM here gets ignored.
        elif args[1] == -3: #ERR_BLACKLISTED
            #self.function_quit()
            self.sendError(-2, "Client black listed. Client shuts down itself")
            os.kill (os.getpid(), SIGKILL) #Somehow a SIGTERM here gets ignored.
        else:
            self.sendError("Client has received error but does not know how to handle it yet. #IMPLEMENT", errorCode, errorMessage) #TODO

    def sendError(self, errorCode, errorMessage):
        errorCode = self.errorCodes[errorCode] #make sure we send a number.
        liblo.send(states.nsmUrl, "/error", NSM_ANNOUNCE, errorCode, errorMessage)


    def fallback(self, path, args, types, src):
        print ("got unknown message '%s' from '%s'" % (path, src.get_url()))
        for a, t in zip(args, types):
            print ("argument of type '%s': %s" % (t, a))

    def _signal_handler(self, signal, frame):
        """Wait for the user to quit the program

        The user function does not need to exit itself.
        Just shutdown audio engines etc.
        If function quit is just pass it will still quit."""
        self.function_quit()
        exit(0)

states = States(os.getenv("NSM_URL"))
ourNsmClient = OurNsmClient(states)

def init(prettyName, capabilities, requiredFunctions, optionalFunctions, sleepValueMs, startsWithGui = True):
    """prettyName = "Super Client"
    Never change the prettyName after your software is ready to use.
    The reported filepath to load and more depends on this. Changing
    this is like telling NSM we are a different program now.
    """
    if not states.nsmUrl:
        raise RuntimeError("Non-Session-Manager environment variable $NSM_URL not found. Only start this program through a session manager")
        exit(1)

    canDo = [key for key,value in capabilities.items() if value]
    capabilitiesString = ":".join([""] + canDo + [""]) if canDo else ""
    states.clientCapabilities = set(canDo)

    for identifier, function in requiredFunctions.items():
        setattr(ourNsmClient, identifier, function)

    for identifier, function in optionalFunctions.items():
        if function:
            setattr(ourNsmClient, identifier, function)

    #Finally tell NSM we are ready and start the main loop
    #__file__ stands for the executable name
    if os.path.dirname(__main__.__file__) in os.environ["PATH"]:
        executableName = os.path.basename(__main__.__file__)
    else:
        executableName = os.path.abspath(__main__.__file__)

    liblo.send(states.nsmUrl, NSM_ANNOUNCE, prettyName, capabilitiesString, executableName, API_VERSION_MAJOR, API_VERSION_MINOR, os.getpid())

    #Wait for the welcome message.
    while not states.welcomeMessage:
        ourNsmClient.libloServer.recv(100)

    #if the optional gui capability is not present then clients with optional-guis MUST always keep them visible
    if "optional-gui" in states.clientCapabilities:
        if not "optional-gui" in states.nsmCapabilities:
            ourNsmClient.function_showGui() #call once. All other osc calls in ourNsmClient will get ignored automatically.
            liblo.send(states.nsmUrl, "/nsm/client/gui_is_shown")
        else:
            if startsWithGui:
                ourNsmClient.function_showGui()
                liblo.send(states.nsmUrl, "/nsm/client/gui_is_shown")
            else:
                ourNsmClient.function_hideGui()
                liblo.send(states.nsmUrl, "/nsm/client/gui_is_hidden")


    return ourNsmClient, lambda: ourNsmClient.libloServer.recv(sleepValueMs) #loop and dispatch messages every 100ms
