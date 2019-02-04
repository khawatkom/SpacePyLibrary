#!/usr/bin/env python3
#******************************************************************************
# (C) 2019, Stefan Korner, Austria                                            *
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
# CCSDS Stack - Unit Tests                                                    *
#******************************************************************************
import testData
import CCSDS.ASSEMBLER, CCSDS.FRAME, CCSDS.PACKET, CCSDS.PACKETIZER
import UTIL.SYS

####################
# global variables #
####################
# Assembler and Packetizer are singletons
s_assembler = None
s_packetizer = None
# the last passed TM packet and TM frame
s_tmBinFrames = []
s_tmBinPackets = []

###########
# classes #
###########
# =============================================================================
class Assembler(CCSDS.ASSEMBLER.Assembler):
  """Subclass of CCSDS.ASSEMBLER.Assembler"""
  def __init__(self):
    """Initialise attributes only"""
    CCSDS.ASSEMBLER.Assembler.__init__(self)
  # ---------------------------------------------------------------------------
  def notifyTMframeCallback(self, binFrame):
    """notifies when the next TM frame is assembled"""
    # overloaded from CCSDS.ASSEMBLER.Assembler
    global s_packetizer, s_tmBinFrames
    s_tmBinFrames.append(binFrame)
    s_packetizer.pushTMframe(binFrame)

# =============================================================================
class Packetizer(CCSDS.PACKETIZER.Packetizer):
  """Subclass of CCSDS.PACKETIZER.Packetizer"""
  def __init__(self):
    """Initialise attributes only"""
    CCSDS.PACKETIZER.Packetizer.__init__(self)
  # ---------------------------------------------------------------------------
  def notifyTMpacketCallback(self, binPacket):
    """notifies when the next TM packet is assembled"""
    # overloaded from CSDS.PACKETIZER.Packetizer
    global s_tmBinPackets
    s_tmBinPackets.append(binPacket)

#############
# functions #
#############
# -----------------------------------------------------------------------------
def initConfiguration():
  """initialise the system configuration"""
  UTIL.SYS.s_configuration.setDefaults([
  ["SPACECRAFT_ID", "758"],
  ["TM_VIRTUAL_CHANNEL_ID", "0"],
  ["TM_TRANSFER_FRAME_SIZE", "1115"],
  ["TM_TRANSFER_FRAME_HAS_SEC_HDR", "0"]])
# -----------------------------------------------------------------------------
def test_setup():
  """setup the environment"""
  global s_assembler, s_packetizer
  # initialise the system configuration
  initConfiguration()
  s_assembler = Assembler()
  s_packetizer = Packetizer()
  return True
# -----------------------------------------------------------------------------
def test_idleFrame():
  """pass an idle frame through Assembler and Packetizer"""
  global s_assembler, s_packetizer, s_tmBinFrames, s_tmBinPackets
  s_tmBinFrames = []
  s_tmBinPackets = []
  s_assembler.flushTMframeOrIdleFrame()
  if len(s_tmBinFrames) != 1:
    print("invalid number of frames")
    return False
  binFrame = s_tmBinFrames[0]
  if len(binFrame) != s_assembler.frameDefaults.transferFrameSize:
    print("expected idle frame has invalid size: " + str(len(binFrame)))
    return False
  tmFrame = CCSDS.FRAME.TMframe(binFrame)
  firstHeaderPointer = tmFrame.firstHeaderPointer
  if firstHeaderPointer != CCSDS.FRAME.IDLE_FRAME_PATTERN:
    print("unexpected frame is no idle frame")
    return False
  if len(s_tmBinPackets) != 0:
    print("unexpected packet passed via idle frame")
    return False
  return True
# -----------------------------------------------------------------------------
def test_singlePacket():
  """pass a single packet through Assembler and Packetizer"""
  global s_assembler, s_packetizer, s_tmBinFrames, s_tmBinPackets
  s_tmBinFrames = []
  s_tmBinPackets = []
  tmPacket = CCSDS.PACKET.TMpacket(testData.TM_PACKET_01)
  s_assembler.pushTMpacket(tmPacket.getBuffer())
  if len(s_tmBinFrames) != 0:
    print("invalid number of frames")
    return False
  if len(s_tmBinPackets) != 0:
    print("invalid number of packets")
    return False
  s_assembler.flushTMframe()
  if len(s_tmBinFrames) != 1:
    print("invalid number of frames")
    return False
  if len(s_tmBinPackets) != 2:
    print("invalid number of packets")
    return False
  binFrame = s_tmBinFrames[0]
  if len(binFrame) != s_assembler.frameDefaults.transferFrameSize:
    print("expected frame has invalid size: " + str(len(binFrame)))
    return False
  receivedTmPacket = CCSDS.PACKET.TMpacket(s_tmBinPackets[0])
  if receivedTmPacket != tmPacket:
    print("packet corrupted during frame assembling and packetizing")
    return False
  receivedTmPacket = CCSDS.PACKET.TMpacket(s_tmBinPackets[1])
  if receivedTmPacket.applicationProcessId != CCSDS.PACKET.IDLE_PKT_APID:
    print("idle packet corrupted during frame assembling and packetizing")
    return False
  return True
# -----------------------------------------------------------------------------
def test_doublePacket():
  """pass 2 packets through Assembler and Packetizer"""
  global s_assembler, s_packetizer, s_tmBinFrames, s_tmBinPackets
  s_tmBinFrames = []
  s_tmBinPackets = []
  tm1Packet = CCSDS.PACKET.TMpacket(testData.TM_PACKET_01)
  s_assembler.pushTMpacket(tm1Packet.getBuffer())
  tm2Packet = CCSDS.PACKET.TMpacket(testData.TM_PACKET_02)
  s_assembler.pushTMpacket(tm2Packet.getBuffer())
  if len(s_tmBinFrames) != 0:
    print("invalid number of frames")
    return False
  if len(s_tmBinPackets) != 0:
    print("invalid number of packets")
    return False
  s_assembler.flushTMframe()
  if len(s_tmBinFrames) != 1:
    print("invalid number of frames")
    return False
  if len(s_tmBinPackets) != 3:
    print("invalid number of packets")
    return False
  binFrame = s_tmBinFrames[0]
  if len(binFrame) != s_assembler.frameDefaults.transferFrameSize:
    print("expected frame has invalid size: " + str(len(binFrame)))
    return False
  receivedTmPacket = CCSDS.PACKET.TMpacket(s_tmBinPackets[0])
  if receivedTmPacket != tm1Packet:
    print("packet 1 corrupted during frame assembling and packetizing")
    return False
  receivedTmPacket = CCSDS.PACKET.TMpacket(s_tmBinPackets[1])
  if receivedTmPacket != tm2Packet:
    print("packet 2 corrupted during frame assembling and packetizing")
    return False
  receivedTmPacket = CCSDS.PACKET.TMpacket(s_tmBinPackets[2])
  if receivedTmPacket.applicationProcessId != CCSDS.PACKET.IDLE_PKT_APID:
    print("idle packet corrupted during frame assembling and packetizing")
    return False
  return True
# -----------------------------------------------------------------------------
def test_spilloverPacket():
  """pass 5 packets to force a spillover packet"""
  global s_assembler, s_packetizer, s_tmBinFrames, s_tmBinPackets
  s_tmBinFrames = []
  s_tmBinPackets = []
  tm1Packet = CCSDS.PACKET.TMpacket(testData.TM_PACKET_01)
  s_assembler.pushTMpacket(tm1Packet.getBuffer())
  tm2Packet = CCSDS.PACKET.TMpacket(testData.TM_PACKET_02)
  s_assembler.pushTMpacket(tm2Packet.getBuffer())
  tm3Packet = CCSDS.PACKET.TMpacket(testData.TM_PACKET_03)
  s_assembler.pushTMpacket(tm3Packet.getBuffer())
  tm4Packet = CCSDS.PACKET.TMpacket(testData.TM_PACKET_02)
  s_assembler.pushTMpacket(tm4Packet.getBuffer())
  tm5Packet = CCSDS.PACKET.TMpacket(testData.TM_PACKET_01)
  s_assembler.pushTMpacket(tm5Packet.getBuffer())
  if len(s_tmBinFrames) != 0:
    print("invalid number of frames")
    return False
  if len(s_tmBinPackets) != 0:
    print("invalid number of packets")
    return False
  tm6Packet = CCSDS.PACKET.TMpacket(testData.TM_PACKET_02)
  s_assembler.pushTMpacket(tm6Packet.getBuffer())
  if len(s_tmBinFrames) != 1:
    print("invalid number of frames")
    return False
  if len(s_tmBinPackets) != 5:
    print("invalid number of packets")
    return False
  s_assembler.flushTMframe()
  if len(s_tmBinFrames) != 2:
    print("invalid number of frames")
    return False
  if len(s_tmBinPackets) != 7:
    print("invalid number of packets")
    return False
  binFrame = s_tmBinFrames[0]
  if len(binFrame) != s_assembler.frameDefaults.transferFrameSize:
    print("expected frame 1 has invalid size: " + str(len(binFrame)))
    return False
  binFrame = s_tmBinFrames[1]
  if len(binFrame) != s_assembler.frameDefaults.transferFrameSize:
    print("expected frame 2 has invalid size: " + str(len(binFrame)))
    return False
  receivedTmPacket = CCSDS.PACKET.TMpacket(s_tmBinPackets[0])
  if receivedTmPacket != tm1Packet:
    print("packet 1 corrupted during frame assembling and packetizing")
    return False
  receivedTmPacket = CCSDS.PACKET.TMpacket(s_tmBinPackets[1])
  if receivedTmPacket != tm2Packet:
    print("packet 2 corrupted during frame assembling and packetizing")
    return False
  receivedTmPacket = CCSDS.PACKET.TMpacket(s_tmBinPackets[2])
  if receivedTmPacket != tm3Packet:
    print("packet 3 corrupted during frame assembling and packetizing")
    return False
  receivedTmPacket = CCSDS.PACKET.TMpacket(s_tmBinPackets[3])
  if receivedTmPacket != tm4Packet:
    print("packet 4 corrupted during frame assembling and packetizing")
    return False
  receivedTmPacket = CCSDS.PACKET.TMpacket(s_tmBinPackets[4])
  if receivedTmPacket != tm5Packet:
    print("packet 5 corrupted during frame assembling and packetizing")
    return False
  receivedTmPacket = CCSDS.PACKET.TMpacket(s_tmBinPackets[5])
  if receivedTmPacket != tm6Packet:
    print("packet 6 corrupted during frame assembling and packetizing")
    return False
  receivedTmPacket = CCSDS.PACKET.TMpacket(s_tmBinPackets[6])
  if receivedTmPacket.applicationProcessId != CCSDS.PACKET.IDLE_PKT_APID:
    print("idle packet corrupted during frame assembling and packetizing")
    return False
  return True

########
# main #
########
if __name__ == "__main__":
  print("***** test_setup() start")
  retVal = test_setup()
  print("***** test_setup() done:", retVal)
  print("***** test_idleFrame() start")
  retVal = test_idleFrame()
  print("***** test_idleFrame() done:", retVal)
  print("***** test_singlePacket() start")
  retVal = test_singlePacket()
  print("***** test_singlePacket() done:", retVal)
  print("***** test_doublePacket() start")
  retVal = test_doublePacket()
  print("***** test_doublePacket() done:", retVal)
  print("***** test_spilloverPacket() start")
  retVal = test_spilloverPacket()
  print("***** test_spilloverPacket() done:", retVal)
