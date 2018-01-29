# coding=utf-8
import time
import shutil
import os
import threading

from octoprint_octolapse.trigger import GcodeTrigger, TimerTrigger, LayerTrigger
import octoprint_octolapse.utility as utility
from octoprint_octolapse.snapshot import CaptureSnapshot,SnapshotInfo
from octoprint_octolapse.settings import OctolapseSettings, Printer, Stabilization, Camera, Rendering, Snapshot, DebugProfile
from octoprint_octolapse.render import Render
from octoprint_octolapse.gcode import SnapshotGcodeGenerator, SnapshotGcode
from octoprint_octolapse.command import *
from octoprint_octolapse.position import Position

class Timelapse(object):
	
	def __init__(self,octolapseSettings, dataFolder, timelapseFolder
			  , onSnapshotStart = None
			  , onSnapshotEnd = None
			  , onRenderStart = None
			  , onRenderComplete = None
			  , onRenderFail = None
			  , onRenderSynchronizeFail = None
			  , onRenderSynchronizeComplete = None
			  , onRenderEnd = None
			  , onTimelapseStopping = None
			  , onTimelapseStopped = None
			  , onStateChanged = None):
		# config variables - These don't change even after a reset
		self.Settings = octolapseSettings
		self.DataFolder = dataFolder
		self.DefaultTimelapseDirectory =  timelapseFolder
		self.OnRenderStartCallback = onRenderStart
		self.OnRenderCompleteCallback = onRenderComplete
		self.OnRenderFailCallback = onRenderFail
		self.OnRenderingSynchronizeFailCallback = onRenderSynchronizeFail
		self.OnRenderingSynchronizeCompleteCallback = onRenderSynchronizeComplete
		self.OnRenderEndCallback = onRenderEnd
		self.OnSnapshotStartCallback = onSnapshotStart
		self.OnSnapshotCompleteCallback = onSnapshotEnd
		self.TimelapseStoppingCallback = onTimelapseStopping
		self.TimelapseStoppedCallback = onTimelapseStopped
		self.OnStateChangedCallback = onStateChanged
		self.Responses = Responses() # Used to decode responses from the 3d printer
		self.Commands = Commands() # used to parse and generate gcode
		
		# Settings that may be different after StartTimelapse is called
		self.FfMpegPath = None
		self.Snapshot = None
		self.Gcode = None
		self.Printer = None
		self.CaptureSnapshot = None
		self.Position = None

		# State Tracking that should only be reset when starting a timelapse
		self.IsRendering = False

		# State tracking variables
		self.Reset()


		
	def StartTimelapse(self,octoprintPrinter, octoprintPrinterProfile, ffmpegPath,g90InfluencesExtruder):
		self.Reset()
		self.OctoprintPrinter = octoprintPrinter
		self.OctoprintPrinterProfile = octoprintPrinterProfile
		self.FfMpegPath = ffmpegPath
		self.PrintStartTime=time.time()
		self.Snapshot = Snapshot(self.Settings.CurrentSnapshot())
		self.Gcode = SnapshotGcodeGenerator(self.Settings,octoprintPrinterProfile)
		self.Printer = Printer(self.Settings.CurrentPrinter())
		self.Rendering = Rendering(self.Settings.CurrentRendering())
		self.CaptureSnapshot = CaptureSnapshot(self.Settings,  self.DataFolder, printStartTime=self.PrintStartTime)
		self.Position = Position(self.Settings,octoprintPrinterProfile, g90InfluencesExtruder)
		self.State = TimelapseState.WaitingForTrigger



		self.IsTestMode = self.Settings.CurrentDebugProfile().is_test_mode
		# create the triggers
		# If the gcode trigger is enabled, add it
		if(self.Snapshot.gcode_trigger_enabled):
			#Add the trigger to the list
			self.Triggers.append(GcodeTrigger(self.Settings))
		# If the layer trigger is enabled, add it
		if(self.Snapshot.layer_trigger_enabled):
			self.Triggers.append(LayerTrigger(self.Settings))
		# If the layer trigger is enabled, add it
		if(self.Snapshot.timer_trigger_enabled):
			self.Triggers.append(TimerTrigger(self.Settings))

	def Reset(self):
		self.State = TimelapseState.Idle
		self.Triggers = []
		self.CommandIndex = -1
		self.SnapshotCount = 0
		self.PrintStartTime = None
		self.SnapshotGcodes = None
		self.SavedCommand = None
		self.PositionRequestAttempts = 0
		self.IsTestMode = False
		# time tracking - how much time did we add to the print?
		self.SecondsAddedByOctolapse = 0
		self.ReturnPositionReceivedTime = None
		# A list of callbacks who want to be informed when a timelapse ends
		self.TimelapseStopRequested = False
		self.SnapshotSuccess = False
		self.SnapshotError = ""
	def ResetSnapshot(self):
		self.State = TimelapseState.WaitingForTrigger
		self.CommandIndex = -1
		self.SnapshotGcodes = None
		self.SavedCommand = None
		self.PositionRequestAttempts = 0
		self.SnapshotSuccess = False
		self.SnapshotError = ""
	def PrintPaused(self):
		if(self.State == TimelapseState.Idle):
			return
		elif(self.State == TimelapseState.WaitingForTrigger):
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Print Paused.")
			if(self.Triggers is not None):
				for trigger in self.Triggers:
					if(type(trigger) == TimerTrigger):
						trigger.Pause()

	def IsTimelapseActive(self):
		if(
			self.State == TimelapseState.Idle
			or self.State == TimelapseState.WaitingToRender
			or len(self.Triggers)<1
		):
			return False
		return True

	def ReturnGcodeCommandToOctoprint(self, cmd):

		if(cmd is None or cmd == (None,)):
			return cmd

		if(self.IsTestMode and self.State >= TimelapseState.WaitingForTrigger):
			return self.Commands.AlterCommandForTestMode(cmd)
		# if we were given a list, return it.
		if(isinstance(cmd,list)):
			return cmd
		# if we were given a command return None (don't change the command at all)
		return None
	
	def GcodeQueuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogQueuingGcode("Queuing Command: Command Type:{0}, gcode:{1}, cmd: {2}".format(cmd_type, gcode, cmd))
		# update the position tracker so that we know where all of the axis are.
		# We will need this later when generating snapshot gcode so that we can return to the previous
		# position
		cmd = cmd.upper().strip()
		self.Position.Update(cmd)
		# if there has been a position or extruder state change, inform any listener
		if(self.OnStateChangedCallback is not None):
			changeDict = {
				"Extruder": None,
				"Position": None 
				}
			if(self.Position.HasStateChanged()):
				changeDict["Position"] = self.Position.ToDict();
			if(self.Position.Extruder.HasChanged()):
				changeDict["Extruder"] = self.Position.Extruder.ToDict();

			if(changeDict["Extruder"] is not None or changeDict["Position"] is not None):
				self.OnStateChangedCallback(changeDict)
			

		isSnapshotGcodeCommand = self.IsSnapshotCommand(cmd)

		if(self.State == TimelapseState.WaitingForTrigger):
			if(self.GcodeQueuing_IsTriggering(cmd,isSnapshotGcodeCommand)):
				# Undo the last position update, we're not going to be using it!
				self.Position.UndoUpdate()
				# Store the current position (our previous position), since this will be our snapshot position
				self.Position.SavePosition()
				# we don't want to execute the current command.  We have saved it for later.
				# but we don't want to send the snapshot command to the printer, or any of the SupporessedSavedCommands (gcode.py)
				if(isSnapshotGcodeCommand or cmd in self.Commands.SuppressedSavedCommands):
					self.SavedCommand = None # this will suppress the command since it won't be added to our snapshot commands list
				else:
					if(self.IsTestMode):
						cmd = self.Commands.GetTestModeCommandString(cmd)
					self.SavedCommand = cmd; # this will cause the command to be added to the end of our snapshot commands
				# pause the printer to start the snapshot
				self.State = TimelapseState.RequestingReturnPosition
					
				# Pausing the print here will immediately trigger an M400 and a location request
				self.OctoprintPrinter.pause_print() # send M400 and position request
				# send a notification to the client that the snapshot is starting
				if(self.OnSnapshotStartCallback is not None):
					self.OnSnapshotStartCallback()
				return None,
				
		elif(self.State > TimelapseState.WaitingForTrigger and self.State < TimelapseState.SendingReturnGcode):
			# Don't do anything further to any commands unless we are taking a timelapse , or if octolapse paused the print.	
			# suppress any commands we don't, under any cirumstances, to execute while we're taking a snapshot
			if(cmd in self.Commands.SuppressedSnapshotGcodeCommands):
				return None, # suppress the command

		if(isSnapshotGcodeCommand ):
			# in all cases do not return the snapshot command to the printer.  It is NOT a real gcode and could cause errors.
			return None,

		return self.ReturnGcodeCommandToOctoprint(cmd)

	def GcodeQueuing_IsTriggering(self,cmd,isSnapshotGcodeCommand):
		currentTrigger = self.IsTriggering(cmd)
		if(currentTrigger is not None):#We're triggering
			self.Settings.CurrentDebugProfile().LogTriggering("A snapshot is triggering")
			
			return True
		elif (self.IsTriggerWaiting(cmd)):
			self.Settings.CurrentDebugProfile().LogTriggerWaitState("Trigger is Waiting On Extruder.")
		return False
	def GcodeSent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogSentGcode("Sent to printer: Command Type:{0}, gcode:{1}, cmd: {2}".format(cmd_type, gcode, cmd))
	
	def IsSnapshotCommand(self, command):
		commandName = GetGcodeFromString(command)
		snapshotCommandName = GetGcodeFromString(self.Printer.snapshot_command)
		return commandName == snapshotCommandName

	def IsTriggering(self,cmd):
		# make sure we're in a state that could want to check for triggers
		if(not self.State == TimelapseState.WaitingForTrigger):
			return None
		# check the command to see if it's a debug assrt

		# Loop through all of the active currentTriggers
		for currentTrigger in self.Triggers:
			# determine what type the current trigger is and update appropriately
			if(isinstance(currentTrigger,GcodeTrigger)):
				currentTrigger.Update(self.Position,cmd)
			elif(isinstance(currentTrigger,TimerTrigger)):
				currentTrigger.Update(self.Position)
			elif(isinstance(currentTrigger,LayerTrigger)):
				currentTrigger.Update(self.Position)
			# see if the current trigger is triggering, indicting that a snapshot should be taken
			if(currentTrigger.IsTriggered):
				# Make sure there are no position errors (unknown position, out of bounds, etc)
				if(not self.Position.HasPositionError()):
					#Triggering!
					return currentTrigger
				else:
					self.Settings.CurrentDebugProfile().LogTriggering("A position error prevented a snapshot trigger!")
		return None
	def IsTriggerWaiting(self,cmd):
		# make sure we're in a state that could want to check for triggers
		if(not self.State == TimelapseState.WaitingForTrigger):
			return None
		isWaiting = False;
		# Loop through all of the active currentTriggers
		for currentTrigger in self.Triggers:
			if(currentTrigger.IsWaiting):
				return True
		return False

	def PositionReceived(self, payload):
		x=payload["x"]
		y=payload["y"]
		z=payload["z"]
		e=payload["e"]
				
		if(self.State == TimelapseState.RequestingReturnPosition):
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Snapshot return position received by Octolapse.")
			self.PositionReceived_Return(x,y,z,e)
		elif(self.State == TimelapseState.SendingSnapshotGcode):
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Snapshot position received by Octolapse.")
			self.PositionReceived_Snapshot(x,y,z,e)
		elif(self.State == TimelapseState.SendingReturnGcode):
			self.PositionReceived_ResumePrint(x,y,z,e)
		else:
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Position received by Octolapse while paused, but was declined.")
			return False, "Declined - Incorrect State"


	def PositionReceived_Return(self, x,y,z,e):
		
		self.ReturnPositionReceivedTime = time.time()
		#todo:  Do we need to re-request the position like we do for the return?  Maybe...
		printerTolerance = self.Printer.printer_position_confirmation_tolerance
		# If we are requesting a return position we have NOT yet executed the command that triggered the snapshot.
		# Because of this we need to compare the position we received to the previous position, not the current one.
		if( not self.Position.IsAtSavedPosition(x,y,z) ):
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("The snapshot return position recieved from the printer does not match the position expected by Octolapse.  received (x:{0},y:{1},z:{2}), Expected (x:{3},y:{4},z:{5})".format(x,y,z,self.Position.X(),self.Position.Y(),self.Position.Z()))
			self.Position.UpdatePosition(x=x,y=y,z=z,force=True)
		else:
			# return position information received
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Snapshot return position received - x:{0},y:{1},z:{2},e:{3}".format(x,y,z,e))
		# make sure the SnapshotCommandIndex = 0
		# Todo: ensure this is unnecessary
		self.CommandIndex=0

		# create the GCode for the timelapse and store it
		isRelative = self.Position.IsRelative()
		isExtruderRelative = self.Position.IsExtruderRelative()

		self.SnapshotGcodes = self.Gcode.CreateSnapshotGcode(x,y,z, self.Position.F(), self.Position.IsRelative(), self.Position.IsExtruderRelative(), self.Position.Extruder, self.Position.DistanceToZLift(), savedCommand=self.SavedCommand)
		# make sure we acutally received gcode
		if(self.SnapshotGcodes is None):
			self.Settings.CurrentDebugProfile().LogSnapshotGcode("No snapshot gcode was created for this snapshot.  Aborting this snapshot.")
			self.ResetSnapshot();
			return False, "Error - No Snapshot Gcode";

		self.State = TimelapseState.SendingSnapshotGcode

		snapshotCommands = self.SnapshotGcodes.SnapshotCommands()

		# send our commands to the printer
		# these commands will go through queuing, no reason to track position
		self.OctoprintPrinter.commands(snapshotCommands)

	def PositionReceived_Snapshot(self, x,y,z,e):
		# snapshot position information received
		self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Snapshot position received, checking position:  Received: x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5},z:{6}".format(x,y,z,e,self.SnapshotGcodes.X,self.SnapshotGcodes.Y, self.Position.Z()))
		printerTolerance = self.Printer.printer_position_confirmation_tolerance
		# see if the CURRENT position is the same as the position we received from the printer
		# AND that it is equal to the snapshot position
		if(not self.Position.IsAtCurrentPosition(x,y,None)):
			self.Settings.CurrentDebugProfile().LogSnapshotPosition("The snapshot position is incorrect.")

		elif(not self.Position.IsAtCurrentPosition(self.SnapshotGcodes.X,self.SnapshotGcodes.Y,None, applyOffset = False)): # our snapshot gcode will NOT be offset
			self.Settings.CurrentDebugProfile().LogSnapshotPosition("The snapshot position matched the expected position (x:{0} y:{1}), but the SnapshotGcode object coordinates don't match the expected position.".format(x,y))
		self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("The snapshot position is correct, taking snapshot.")
		self.State = TimelapseState.TakingSnapshot
		self.TakeSnapshot()

	def PositionReceived_ResumePrint(self, x,y,z,e):
		if(not self.Position.IsAtCurrentPosition(x,y,None)):
			self.Settings.CurrentDebugProfile().LogSnapshotPositionResumePrint("Save Command Position is incorrect.  Received: x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5},z:{6}".format(x,y,z,e,self.Position.X(),self.Position.Y(), self.Position.Z()))
		else:
			self.Settings.CurrentDebugProfile().LogSnapshotPositionResumePrint("Save Command Position is correct.  Received: x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5},z:{6}".format(x,y,z,e,self.Position.X(),self.Position.Y(), self.Position.Z()))

		self.SecondsAddedByOctolapse += time.time() - self.ReturnPositionReceivedTime

		# before resetting the snapshot, see if it was a success
		snapshotSuccess = self.SnapshotSuccess
		snapshotError = self.SnapshotError
		# end the snapshot
		self.ResetSnapshot()

		# If we've requested that the timelapse stop, stop it now
		if(self.TimelapseStopRequested):
			self.StopSnapshots()

		self.OctoprintPrinter.resume_print()

		if(self.OnSnapshotCompleteCallback is not None):
			payload = {
					"success": snapshotSuccess,
					"error" : snapshotError,
					"snapshot_count" : self.SnapshotCount,
					"seconds_added_by_octolapse" : self.SecondsAddedByOctolapse
				}
			self.OnSnapshotCompleteCallback(payload)

	def TakeSnapshot(self):
		
		self.Settings.CurrentDebugProfile().LogSnapshotDownload("Taking Snapshot.")
		try:
			self.CaptureSnapshot.Snap(utility.CurrentlyPrintingFileName(self.OctoprintPrinter),self.SnapshotCount,onComplete = self.OnSnapshotComplete, onSuccess = self.OnSnapshotSuccess, onFail = self.OnSnapshotFail)
			
		except:
			a = sys.exc_info() # Info about unknown error that caused exception.                                              
			errorMessage = "    {0}".format(a)
			b = [ str(p) for p in a ]
			errorMessage += "\n    {0}".format(b)
			self.Settings.CurrentDebugProfile().LogSnapshotSave('Unknown error detected:{0}'.format(errorMessage))
		
	def OnSnapshotSuccess(self, *args, **kwargs):
		# Increment the number of snapshots received
		self.SnapshotCount += 1
		# get the save path
		snapshotInfo = args[0]
		# get the current file name
		newSnapshotName = snapshotInfo.GetFullPath(self.SnapshotCount)
		self.Settings.CurrentDebugProfile().LogSnapshotSave("Renaming snapshot {0} to {1}".format(snapshotInfo.GetTempFullPath(),newSnapshotName))
		# create the output directory if it does not exist
		try:
			path = os.path.dirname(newSnapshotName)
			if not os.path.exists(path):
				os.makedirs(path)
		except:
			type = sys.exc_info()[0]
			value = sys.exc_info()[1]
			self.Settings.CurrentDebugProfile().LogSnapshotSave("An exception was thrown when trying to create a directory for the downloaded snapshot: {0}  , ExceptionType:{1}, Exception Value:{2}".format(os.path.dirname(dir),type,value))
			return

		# rename the current file
		try:

			shutil.move(snapshotInfo.GetTempFullPath(),newSnapshotName)
			self.SnapshotSuccess = True
		except:
			type = sys.exc_info()[0]
			value = sys.exc_info()[1]
			message = "Could rename the snapshot {0} to {1}!   Error Type:{2}, Details:{3}".format(snapshotInfo.GetTempFullPath(), newSnapshotName,type,value)
			self.Settings.CurrentDebugProfile().LogSnapshotSave(message)
			self.SnapshotSuccess = False
			self.SnapshotError = message
	def OnSnapshotFail(self, *args, **kwargs):
		reason = args[0]
		message = "Failed to download the snapshot.  Reason:{0}".format(reason)
		self.Settings.CurrentDebugProfile().LogSnapshotDownload(message)
		self.SnapshotSuccess = False
		self.SnapshotError = message
	def OnSnapshotComplete(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogSnapshotDownload("Snapshot Completed.")
		self.SendReturnCommands()
		
		
	def SendReturnCommands(self):
		# Expand the current command to include the return commands
		returnCommands = self.SnapshotGcodes.ReturnCommands()
		# set the state so that the final received position will trigger a resume.
		self.State = TimelapseState.SendingReturnGcode
		# these commands will go through queuing, no need to update the position
		self.OctoprintPrinter.commands(returnCommands)
		

	def StopSnapshots(self):
		"""Stops octolapse from taking any further snapshots.  Any existing snapshots will render after the print is ends."""
		# we don't need to end the timelapse if it hasn't started
		if(self.State == TimelapseState.WaitingForTrigger or self.TimelapseStopRequested):
			self.State = TimelapseState.WaitingToRender
			self.TimelapseStopRequested = False
			if(self.TimelapseStoppedCallback is not None):
				self.TimelapseStoppedCallback()
			return True
		
		# if we are here, we're delaying the request until after the snapshot
		self.TimelapseStopRequested = True
		if(self.TimelapseStoppingCallback is not None):
			self.TimelapseStoppingCallback()

	def EndTimelapse(self):
		if(not self.State == TimelapseState.Idle):
			self.RenderTimelapse()
			self.Reset();
			
	def RenderTimelapse(self):
		# make sure we have a non null TimelapseSettings object.  We may have terminated the timelapse for some reason
		if(self.Rendering.enabled):
			self.Settings.CurrentDebugProfile().LogRenderStart("Started Rendering Timelapse");
			# we are rendering, set the state before starting the rendering job.
			self.IsRendering = True
			timelapseRenderJob = Render(self.Settings
									,self.Snapshot
									,self.Rendering
								  ,self.DataFolder
								  ,self.DefaultTimelapseDirectory
								  ,self.FfMpegPath
								  ,1
								  ,timeAdded = self.SecondsAddedByOctolapse
								  ,onRenderStart = self.OnRenderStart
								  ,onRenderFail=self.OnRenderFail
								  ,onRenderSuccess = self.OnRenderSuccess
								  ,onRenderComplete = self.OnRenderComplete
								  ,onAfterSyncFail = self.OnSynchronizeRenderingFail
								  ,onAfterSycnSuccess = self.OnSynchronizeRenderingComplete
								  ,onComplete = self.OnRenderEnd)
			timelapseRenderJob.Process(utility.CurrentlyPrintingFileName(self.OctoprintPrinter), self.PrintStartTime, time.time())
			
			return True
		return False

	def OnRenderStart(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogRenderStart("Started rendering/synchronizing the timelapse.")
		finalFilename = args[0]
		baseFileName = args[1]
		willSync = args[2]
		snapshotCount = args[3]
		snapshotTimeSeconds = args[4]
		
		payload = dict(
			FinalFileName = finalFilename
			, WillSync = willSync
			, SnapshotCount = snapshotCount
			, SnapshotTimeSeconds = snapshotTimeSeconds)
		# notify the caller
		if(self.OnRenderStartCallback is not None):
			self.OnRenderStartCallback(payload)

	def OnRenderFail(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogRenderFail("The timelapse rendering failed.")
		#Notify Octoprint
		finalFilename = args[0]
		baseFileName = args[1]
		returnCode = args[2]
		reason = args[3]
		
		payload = dict(gcode="unknown",
				movie=finalFilename,
				movie_basename=baseFileName ,
				returncode=returnCode,
				reason = reason)

		if(self.OnRenderFailCallback is not None):
			self.OnRenderFailCallback(payload)
		
	def OnRenderSuccess(self, *args, **kwargs):
		finalFilename = args[0]
		baseFileName = args[1]
		#TODO:  Notify the user that the rendering is completed if we are not synchronizing with octoprint
		self.Settings.CurrentDebugProfile().LogRenderComplete("Rendering completed successfully.")

	def OnRenderComplete(self, *args, **kwargs):
		finalFileName = args[0]
		synchronize = args[1]
		self.IsRendering = False
		self.Settings.CurrentDebugProfile().LogRenderComplete("Completed rendering the timelapse.")
	# Synchronize renderings with the default plugin
	def OnSynchronizeRenderingComplete(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogRenderComplete("Synchronization with octoprint completed successfully.")

	def OnSynchronizeRenderingFail(self, *args, **kwargs):
		finalFilename = args[0]
		baseFileName = args[1]
		# Notify the user of success and refresh the default timelapse control
		payload = dict(gcode="unknown",
				movie=finalFilename,
				movie_basename=baseFileName ,
				reason="Error copying the rendering to the Octoprint timelapse folder.  If logging is enabled you can search for 'Synchronization Error' to find the error.  Your timelapse is likely within the octolapse data folder.")

		if(self.OnRenderingSynchronizeFailCallback is not None):
			self.OnRenderingSynchronizeFailCallback(payload)
	def OnSynchronizeRenderingComplete(self, *args, **kwargs):
		finalFilename = args[0]
		baseFileName = args[1]
		# Notify the user of success and refresh the default timelapse control
		payload = dict(gcode="unknown",
				movie=finalFilename,
				movie_basename=baseFileName ,
				movie_prefix="from Octolapse.  Your timelapse has been synchronized and is now available within the default timelapse plugin tab.",
				returncode=0,
				reason="See the octolapse log for details.")
		if(self.OnRenderingSynchronizeCompleteCallback is not None):
			self.OnRenderingSynchronizeCompleteCallback(payload)

	def OnRenderEnd(self, *args, **kwargs):
		finalFileName = args[0]
		baseFileName = args[1]
		synchronize = args[2]
		success = args[3]
		self.Settings.CurrentDebugProfile().LogRenderComplete("Completed rendering.")
		moviePrefix = "from Octolapse"
		if(not synchronize):
			moviePrefix = "from Octolapse.  Your timelapse was NOT synchronized (see advanced rendering settings for details), but can be found in octolapse's data directory.  A file browser will be added in a future release (hopefully)"
		payload = dict(movie=finalFileName,
				movie_basename=baseFileName ,
				movie_prefix=moviePrefix,
				success=success)
		if(self.OnRenderEndCallback is not None):
			self.OnRenderEndCallback(payload)



	
class TimelapseState(object):
	Idle = 1
	WaitingForTrigger = 2
	RequestingReturnPosition = 3
	SendingSnapshotGcode = 4
	TakingSnapshot = 5
	SendingReturnGcode = 6
	WaitingToRender = 7
