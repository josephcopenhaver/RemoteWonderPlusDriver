import usb.core, win32api, win32con, time, sys, traceback
#E:\Programs\Python27\Lib\site-packages\win32\lib\win32con.py

class MouseEvent():

	def __init__(self, downID, upID=None):
		self.downID = downID
		self.upID = upID

	def __str__(self):
		downID = self.downID
		if downID is None:
			downID = 'None'
		upID = self.upID
		if upID is None:
			upID = 'None'
		return "MouseEvent(UP#%s,DOWN#%s)"%(downID, upID)

class KeyEvent():

	def __init__(self, id):
		self.id = id

	def __str__(self):
		return "KeyEvent#%s"%(self.id)

class RemoteWonderPlusDriver:

	deviceName = 'ATI Wonder Plus RF Remote Control'
	readTimeoutMilliseconds = 3000
	numBytesToRead = 4
	toggleMask = 0x0080
	codeMask = 0x8080^0xFFFF
	nonRepeatingInterReadDelaySeconds = 0.20
	devicePresentCheckIntervalSeconds = 3
	stdSeconds = 0.05
	mousePixelStep = 5
	repeatingMousePixelStep = 20

	# AUTO_CONFIG

	buttonCodeMap = {
		'A':                  0x4500,
		'ACCEPT':             0x5D18,
		'B':                  0x4601,
		'C':                  0x5E19,
		'CHANNEL_DOWN':       0x510C,
		'CHANNEL_UP':         0x500B,
		'D':                  0x601B,
		'DOWN':               0x6722,
		'DVD':                0x4904,
		'E':                  0x6621,
		'EIGHT':              0x5914,
		'ENTER':              0x631E,
		'F':                  0x6823,
		'FAST_FORWARD':       0x6B26,
		'FIVE':               0x5611,
		'FM':                 0x611C,
		'FOUR':               0x5510,
		'GRAB':               0x4C07,
		'GUIDE':              0x4B06,
		'INFORMATION':        0x712C,
		'LEFT':               0x621D,
		'MENU':               0x5B16,
		'NINE':               0x5A15,
		'NO':                 0x417C,
		'ONE':                0x520D,
		'OPEN_MEDIA_CENTER':  0x722D,
		'PAUSE':              0x6E29,
		'PICTURE_IN_PICTURE': 0x6520,
		'PLAY':               0x6A25,
		'POWER':              0x4702,
		'QUESTION_MARK':      0x4A05,
		'RECORD':             0x6C27,
		'REWIND':             0x6924,
		'RIGHT':              0x641F,
		'SEVEN':              0x5813,
		'SIX':                0x5712,
		'STOP':               0x6D28,
		'THREE':              0x540F,
		'TILT_DOWN':          0x3873,
		'TILT_DOWN_LEFT':     0x3C77,
		'TILT_DOWN_RIGHT':    0x3B76,
		'TILT_LEFT':          0x3570,
		'TILT_RIGHT':         0x3671,
		'TILT_UP':            0x3772,
		'TILT_UP_LEFT':       0x3974,
		'TILT_UP_RIGHT':      0x3A75,
		'TIME':               0x702B,
		'TV':                 0x4803,
		'TV2':                0x6F2A,
		'TWO':                0x530E,
		'UP':                 0x5F1A,
		'VOLUME_DOWN':        0x4E09,
		'VOLUME_MUTE':        0x4F0A,
		'VOLUME_UP':          0x4D08,
		'YES':                0x3D78,
		'ZERO':               0x5C17
	}

	keyDownStatesDict = {
		None:True,
		'd':True,
		'down':True,
		'du':True,
		'down_up':True
	}

	keyUpStatesDict = {
		None:True,
		'u':True,
		'up':True,
		'du':True,
		'down_up':True
	}

	readTimeoutSeconds = readTimeoutMilliseconds / 1000
	codeButtonMap = dict([[v,k] for k,v in buttonCodeMap.items()])
	
	def __init__(self, actionMap={}, stdSeconds=None, mousePixelStep=None, repeatingMousePixelStep=None):
		self.actionMap = actionMap
		self.lastCode = 0
		self.lastReadFailTime = 0
		self.lastReadTimeSeconds = 0
		self.lastToggleState = False
		self.stdSeconds = (stdSeconds is None and (self.__class__.stdSeconds,) or (stdSeconds,))[0]
		self.mousePixelStep = (mousePixelStep is None and (self.__class__.mousePixelStep,) or (mousePixelStep,))[0]
		self.repeatingMousePixelStep = (repeatingMousePixelStep is None and (self.__class__.repeatingMousePixelStep,) or (repeatingMousePixelStep,))[0]
		self.repeatModeEnabled = False
	#end def __init__
	
	def getMousePixelStep(self):
		if self.repeatModeEnabled:
			return self.repeatingMousePixelStep
		else:
			return self.mousePixelStep
	#end def mousePixelStep

	def fireEvent(self, eventID, state=None, modifiers=None, stdSeconds=None):
		originalEventID = eventID
		sendDownState = (state in self.__class__.keyDownStatesDict)
		sendUpState = (state in self.__class__.keyUpStatesDict)
		#check if mouse button
		eventEnums = [None, None]
		mouseButton = False
		if isinstance(eventID, KeyEvent):
			eventEnums[0] = eventID.id
		elif isinstance(eventID, MouseEvent):
			mouseButton = True
			eventEnums[0] = eventID.downID
			eventEnums[1] = eventID.upID
		else:
			#check for explicit mouse button
			eventID = eventID.upper()
			if len(eventID) > 6 and eventID[0:6] == 'MOUSE_':
				mouseButton = True
				eventID = eventID[6:]
			if not mouseButton:
				# check for keyboard button
				try:
					eventEnums[0] = getattr(win32con, 'VK_' + eventID)
				except:
					try:
						eventEnums[0] = getattr(win32con, 'WM_' + eventID)
					except:
						pass
			if eventEnums[0] is None:
				#check for mouse button
				if sendDownState:
					try:
						eventEnums[0] = getattr(win32con, 'MOUSEEVENTF_' + eventID + 'DOWN')
						mouseButton = True
					except:
						pass
				if sendUpState:
					try:
						eventEnums[1] = getattr(win32con, 'MOUSEEVENTF_' + eventID + 'UP')
						mouseButton = True
					except:
						pass
		if (sendDownState or not mouseButton) and eventEnums[0] is None:
			if sendDownState:
				unknownState = 'down'
			else:
				unknownState = 'up'
		elif mouseButton and sendUpState and eventEnums[1] is None:
			unknownState = 'up'
		else:
			unknownState = None
		if unknownState is not None:
			raise ValueError("Cannot fire %s event \"%s\", state \"%s\""%((mouseButton and ('MOUSE',) or ('KEY',))[0], originalEventID, unknownState))
		doDelay = (sendDownState and sendUpState)
		if sendDownState:
			if mouseButton:
				x,y = win32api.GetCursorPos()
				#print "Pressing mouse_%s button"%(eventID)
				win32api.mouse_event(eventEnums[0],x,y,0,0)
			else:
				#print "Pressing %s button"%(eventID)
				win32api.keybd_event(eventEnums[0], 0, 0, 0)
		if doDelay:
			if stdSeconds is None:
				try:
					stdSeconds = self.stdSeconds
				except:
					pass
			if stdSeconds is not None:
				time.sleep(stdSeconds)
		if sendUpState:
			if mouseButton:
				#print "Releasing mouse_%s button"%(eventID)
				if not sendDownState:
					x,y = win32api.GetCursorPos()
				win32api.mouse_event(eventEnums[1],x,y,0,0)
			else:
				#print "Releasing %s button"%(eventID)
				win32api.keybd_event(eventEnums[0], 0, win32con.KEYEVENTF_KEYUP, 0)
	#end def fireEvent

	def run(self):
		ignoreError = False
		ingoreTraceback = False
		while 1:
			#print "Run main driver service loop"
			try:
				dev = usb.core.find(idVendor=0x0BC7, idProduct=0x0004)

				if dev is None:
					ingoreTraceback = True
					raise ValueError('%s not connected!'%(self.__class__.deviceName))

				# set the active configuration. With no arguments, the first
				# configuration will be the active one
				dev.set_configuration()
				cfg = dev.get_active_configuration()

				interface_number = cfg[(0,0)].bInterfaceNumber
				alternate_setting = usb.control.get_interface(dev, interface_number)
				interfaceDescriptor = usb.util.find_descriptor(
					cfg, bInterfaceNumber = interface_number,
					bAlternateSetting = alternate_setting
				)

				inputChannel = usb.util.find_descriptor(
					interfaceDescriptor,
					# match the first IN endpoint
					custom_match = \
					lambda e: \
						usb.util.endpoint_direction(e.bEndpointAddress) == \
						usb.util.ENDPOINT_IN
				)

				try:
					self.handleInput(inputChannel)
				except usb.core.USBError:
					ignoreError = True
					raise
			except KeyboardInterrupt:
				raise
			except usb.core.USBError:
				if not ignoreError:
					raise
				ignoreError = False
				print "%s disconnected!"%(self.__class__.deviceName)
				time.sleep(self.__class__.devicePresentCheckIntervalSeconds)
			except ValueError:
				print sys.exc_info()[1]
				time.sleep(self.__class__.devicePresentCheckIntervalSeconds)
			except:
				err_info = sys.exc_info()
				print err_info[0:2]
				if ingoreTraceback:
					ingoreTraceback = False
				else:
					traceback.print_tb(err_info[2])
				time.sleep(self.__class__.devicePresentCheckIntervalSeconds)
	#end def run

	def handleInput(self, inputChannel):
		print "%s connected!"%(self.__class__.deviceName)
		self.repeatModeEnabled = False
		while 1:
			#print "Handler main loop"
			try:
				#print "Reading at Time: %s"%(time.time())
				if not self.repeatModeEnabled:
					timeToWaitSeconds = self.__class__.nonRepeatingInterReadDelaySeconds - (time.time()-self.lastReadTimeSeconds)
					#print timeToWaitSeconds
					if timeToWaitSeconds > 0:
						time.sleep(timeToWaitSeconds)
				bytesRead = inputChannel.read(self.__class__.numBytesToRead, self.__class__.readTimeoutMilliseconds)
				self.lastReadTimeSeconds = time.time()
			except usb.core.USBError:
				readFailTime = time.time()
				if readFailTime - self.lastReadFailTime < self.__class__.readTimeoutSeconds:
					self.lastReadFailTime = readFailTime
					raise
				self.lastReadFailTime = readFailTime
				continue
			length = len(bytesRead)
			if (length != 4):
				print "DEBUG-Invalid number of bytes read!:%s"%length
				for byte in bytesRead:
					print byte
				raise ValueError("Invalid number of bytes read!")
			beginOfSignal = bytesRead[0]
			endOfSignal = bytesRead[3]
			if (beginOfSignal != 21):
				print "BeginOfSignal Byte: %s!=21, %s, %s, EndOfSignal Byte=%s (should be 240)"%(beginOfSignal, bytesRead[1], bytesRead[2], endOfSignal)
				continue
			if (endOfSignal != 240):
				print "EndOfSignal Byte: %s!=240"%(endOfSignal)
				continue
			code = ((bytesRead[1]<<8)|(bytesRead[2]))
			toggleState = ((code&self.__class__.toggleMask) == self.__class__.toggleMask)
			code = code&self.__class__.codeMask
			previousRepeatModeEnabled = self.repeatModeEnabled
			self.repeatModeEnabled = (code == self.lastCode and toggleState == self.lastToggleState)
			if (self.repeatModeEnabled and not previousRepeatModeEnabled):
				continue;
			buttonName = self.__class__.codeButtonMap[code]
			#print "Button: %s"%(buttonName)
			#
			# Process callbacks
			#
			if buttonName in self.actionMap:
				callback = self.actionMap[buttonName]
				#print "Handling callback"
				try:
					if isinstance(callback, str) or isinstance(callback, KeyEvent) or isinstance(callback, MouseEvent):
						self.fireEvent(callback)
					else:
						callback()
				except:
					print "Callback for button \"%s\" threw error:"%(buttonName)
					err_info = sys.exc_info()
					print err_info[1]
					traceback.print_tb(err_info[2])
			else:
				print "Button \"%s\" has no action assigned!"%(buttonName)
			#
			# Store deltas
			#
			self.lastCode = code
			self.lastToggleState = toggleState
	#end def handleInput
#end class RemoteWonderPlusDriver

if __name__ == '__main__':
	driverInstance = RemoteWonderPlusDriver()
	begin = lambda *args: args[-1]
	fireEvent = lambda *args, **kwargs:driverInstance.fireEvent(*args, **kwargs)
	def moveMouse(dx, dy):
		win32api.mouse_event(win32con.MOUSEEVENTF_MOVE,dx,dy,0,0)
	#end def moveMouse
	passThroughActions = [
		'UP',
		'DOWN',
		'LEFT',
		'RIGHT',
		'ENTER',
		'VOLUME_UP',
		'VOLUME_DOWN',
		'RECORD',
		'VOLUME_MUTE'
	]
	lstack = [None]
	def lset(arg):
		lstack[0] = arg
	def lget(idx=0):
		return lstack[idx]
	def lpop(idx=0):
		ref = lstack[idx]
		lstack[idx] = None
		return ref
	actions = {
		'C':                lambda:begin(# ALT_TAB... supposedly... but not working
		                        fireEvent(KeyEvent(56), 'd'),# ALT_DOWN
								fireEvent('tab'),
		                        fireEvent(KeyEvent(56), 'u')# ALT_UP
		                    ),
		'YES':             'mouse_left',
		'NO':              'mouse_right',
		'D':               'escape',
		'TILT_UP':         lambda:moveMouse(0, -driverInstance.getMousePixelStep()),
		'TILT_DOWN':       lambda:moveMouse(0, driverInstance.getMousePixelStep()),
		'TILT_LEFT':       lambda:moveMouse(-driverInstance.getMousePixelStep(), 0),
		'TILT_RIGHT':      lambda:moveMouse(driverInstance.getMousePixelStep(), 0),
		'TILT_UP_LEFT':    lambda:begin(lset(driverInstance.getMousePixelStep()),moveMouse(-lget(), -lpop())),
		'TILT_UP_RIGHT':   lambda:begin(lset(driverInstance.getMousePixelStep()),moveMouse(lget(), -lpop())),
		'TILT_DOWN_RIGHT': lambda:begin(lset(driverInstance.getMousePixelStep()),moveMouse(lget(), lpop())),
		'TILT_DOWN_LEFT':  lambda:begin(lset(driverInstance.getMousePixelStep()),moveMouse(-lget(), lpop())),
		'PLAY':            'MEDIA_PLAY_PAUSE',
		'PAUSE':           'SPACE',
		'STOP':            'MEDIA_PLAY_PAUSE',
		'E':               'BROWSER_BACK',
		'F':               'BROWSER_FORWARD',
		'REWIND':          'MEDIA_PREV_TRACK',
		'FAST_FORWARD':    'MEDIA_NEXT_TRACK',
		'MENU':            KeyEvent(93),#CONTEXT_MENU
		'ZERO':            KeyEvent(48),
		'ONE':             KeyEvent(49),
		'TWO':             KeyEvent(50),
		'THREE':           KeyEvent(51),
		'FOUR':            KeyEvent(52),
		'FIVE':            KeyEvent(53),
		'SIX':             KeyEvent(54),
		'SEVEN':           KeyEvent(55),
		'EIGHT':           KeyEvent(56),
		'NINE':            KeyEvent(57),
		'POWER':           'CLOSE'
	}
	for action in passThroughActions:
		actions[action] = action
	driverInstance.actionMap = actions
	driverInstance.run()