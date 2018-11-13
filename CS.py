#!/usr/bin/env python
#******************************************************************************
# (C) 2018, Stefan Korner, Austria                                            *
#                                                                             *
# The Space Python Library is free software; you can redistribute it and/or   *
# modify it under under the terms of the MIT License as published by the      *
# Massachusetts Institute of Technology.                                      *
#                                                                             *
# The Space Python Library is distributed in the hope that it will be useful, *
# but WITHOUT ANY WARRANTY; without even the implied warranty of              *
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the MIT License    *
# for more details.                                                           *
#******************************************************************************
# Control System (CS) implementation                                          *
#                                                                             *
# The system can act as Central Checkout System (CCS)                         *
# or as Mission Control System (MCS).                                         *
#                                                                             *
# The systen supports the following EGSE_PROTOCOLs for CCS connection:        *
# - CNC:  implements CAIT-03474-ASTR_issue_3_EGSE_IRD.pdf                     *
# - EDEN: implements Core_EGSE_AD03_GAL_REQ_ALS_SA_R_0002_EGSE_IRD_issue2.pdf *
# The system supports the following protocol for MCS connection:              *
# - NCTRS/NIS: implements EGOS-NIS-NCTR-ICD-0002-i4r0.2 (Signed).pdf          *
#******************************************************************************
import sys, os
from UTIL.SYS import Error, LOG, LOG_INFO, LOG_WARNING, LOG_ERROR
import MC.IF
import MCUI.CFGgui, MCUI.TMgui, MCUI.TCgui
import UI.TKI
import UTIL.SYS, UTIL.TCO, UTIL.TASK

#############
# constants #
#############
SYS_CONFIGURATION = [
  ["SYS_COLOR_LOG", "1"],
  ["SYS_APP_MNEMO", "CS"],
  ["SYS_APP_NAME", "Control System"],
  ["SYS_APP_VERSION", "3.0"]]

###########
# classes #
###########
# =============================================================================
class ModelTask(UTIL.TASK.ProcessingTask):
  """The CS is the processing model"""
  # ---------------------------------------------------------------------------
  def __init__(self, isParent):
    """Initialise the Task as processing model"""
    UTIL.TASK.ProcessingTask.__init__(self, isParent=isParent)
  # ---------------------------------------------------------------------------
  def notifyGUItask(self, status):
    """Update the GUI task"""
    # pass the view event to the event queue of the parent task
    event = UTIL.TASK.ViewEvent(status)
    event.enable(UTIL.TASK.s_parentTask)
  # ---------------------------------------------------------------------------
  def notifyCommand(self, argv):
    """Entry point for processing"""
    if len(argv) == 0:
      # echo command ---> allways OK
      LOG("echo command")
      return 0
    # decode the command
    cmd = argv[0].upper()
    retStatus = False;
    if (cmd == "H") or (cmd == "HELP"):
      retStatus = self.helpCmd(argv)
    elif (cmd == "Q") or (cmd == "QUIT"):
      retStatus = self.quitCmd(argv)
    elif (cmd == "U") or (cmd == "DUMPCONFIGURATION"):
      retStatus = self.dumpConfigurationCmd(argv)
    else:
      LOG_WARNING("invalid command " + argv[0])
      return -1
    if retStatus:
      # processing successful
      return 0
    # processing error
    return -2
  # ---------------------------------------------------------------------------
  def helpCmd(self, argv):
    """Decoded help command"""
    LOG_INFO("Available configuration commands:", "CFG")
    LOG("", "CFG")
    LOG("x  | exit ...............terminates client connection (only for TCP/IP clients)", "CFG")
    LOG("h  | help ...............provides this information", "CFG")
    LOG("q  | quit ...............terminates SIM application", "CFG")
    LOG("u  | dumpConfiguration...dumps the configuration", "CFG")
    LOG_INFO("Available monitoring commands:", "TM")
    LOG("", "TM")
    LOG("x  | exit ...............terminates client connection (only for TCP/IP clients)", "TM")
    LOG("h  | help ...............provides this information", "TM")
    LOG("q  | quit ...............terminates SIM application", "TM")
    LOG("u  | dumpConfiguration...dumps the configuration", "TM")
    LOG_INFO("Available control commands:", "TC")
    LOG("", "TC")
    LOG("x  | exit ...............terminates client connection (only for TCP/IP clients)", "TC")
    LOG("h  | help ...............provides this information", "TC")
    LOG("q  | quit ...............terminates SIM application", "TC")
    LOG("u  | dumpConfiguration...dumps the configuration", "TC")
    return True
  # ---------------------------------------------------------------------------
  def quitCmd(self, argv):
    """Decoded quit command"""
    self.logMethod("quitCmd")
    UTIL.TASK.s_parentTask.stop()
    return True
  # ---------------------------------------------------------------------------
  def dumpConfigurationCmd(self, argv):
    """Decoded dumpConfiguration command"""
    self.logMethod("dumpConfigurationCmd")
    MC.IF.s_configuration.dump()
    return True

#############
# functions #
#############
# global shortcut functions for test commands
def help(*argv): UTIL.TASK.s_processingTask.helpCmd(("", ) + argv)
def quit(*argv): UTIL.TASK.s_processingTask.quitCmd(("", ) + argv)
def dumpConfiguration(*argv): UTIL.TASK.s_processingTask.dumpConfigurationCmd(("", ) + argv)
# -----------------------------------------------------------------------------
def printUsage(launchScriptName):
  """Prints the possible commandline options of the test driver"""
  print("")
  print("usage:")
  print("------")
  print("")
  print(launchScriptName)
  print("\t[ -i | -interpreter | -c | -cmdprompt | -bg | -background ]")
  print("\t[ -n | -nogui ] [ -p <port> | -port <port> ]")
  print("\t[ -l <logfile> | -logfile <logfile> ] [ -h | -help ]")
  print("")

########
# main #
########
# detect if the application is launched with or without python prompt
if sys.argv[0] == "":
  interpreter = True
  sys.argv = os.getenv("ARGS").split()
  launchScriptName = sys.argv[0]
else:
  interpreter = False
  launchScriptName = sys.argv[1]
# initialise the system configuration
UTIL.SYS.s_configuration.setDefaults(SYS_CONFIGURATION)
MC.IF.s_configuration = MC.IF.Configuration()
# initialise the request handler
requestHandler = UTIL.TASK.RequestHandler(sys.argv)
if requestHandler.helpRequested:
  printUsage(launchScriptName)
  sys.exit(0)
# check specific command line switches
guiMode = True
cmdPrompt = False
for arg in sys.argv:
  cmdSwitch = arg.upper()
  if cmdSwitch == "-N" or cmdSwitch == "-NOGUI":
    guiMode = False
  if cmdSwitch == "-C" or cmdSwitch == "-CMDPROMPT":
    if not interpreter:
      cmdPrompt = True
# initialise the model and the GUI on demand
if guiMode:
  # keep the order: tasks must exist before the gui views are created
  UI.TKI.createGUI()
  guiTask = UI.TKI.GUItask()
  modelTask = ModelTask(isParent=False)
  win0 = UI.TKI.createWindow()
  win1 = UI.TKI.createWindow()
  win2 = UI.TKI.createWindow()
  gui0view = MCUI.CFGgui.GUIview(win0)
  gui1view = MCUI.TMgui.GUIview(win1)
  gui2view = MCUI.TCgui.GUIview(win2)
  UI.TKI.finaliseGUIcreation()
else:
  modelTask = ModelTask(isParent=True)
# register the TCP/IP server socket for remote control
if requestHandler.portNr != 0:
  print("register connect port...")
  if not requestHandler.openConnectPort(UTIL.SYS.s_configuration.HOST):
    sys.exit(-1)
  connectSocket = requestHandler.connectSocket
  modelTask.createFileHandler(connectSocket, requestHandler.tcpConnectCallback)
# register the requestHandler as console handler if requested
if cmdPrompt:
  print("register console handler...")
  modelTask.registerConsoleHandler(requestHandler)

# start the tasks
print("start modelTask...")
modelTask.start()
if guiMode:
  print("start guiTask...")
  guiTask.start()
  print("guiTask terminated")
  modelTask.join()
print("modelTask terminated")
