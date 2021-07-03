#!/usr/bin/python3

import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import cv2 as cv
from adafruit_servokit import ServoKit
import numpy as np
import jetson.inference
import jetson.utils
from components.segnet_utils import *
from pyqt5Custom import ToggleSwitch
from components.servoControl import FollowTarget, MoveServo
import time

# Servo setup
myKit = ServoKit(channels = 16)
tiltMotor = myKit.servo[1]		# Tilt motor
panMotor = myKit.servo[0]		# Pan motor

loadTrackingModel = False
loadDetectionModel = False
loadSegmentationModel = False
loadSegmentationModelSignal = 1
automaticTracking = False

def loadModels():
	"""
	Load session data
	"""
	global tracker, detectionNet, segmentationNet, segmentationNet, buffers
	tracker = cv.TrackerCSRT_create()
	detectionNet = jetson.inference.detectNet("ssd-mobilenet-v2", threshold = 0.5)
	segmentationNet = jetson.inference.segNet("fcn-resnet18-sun")
	segmentationNet.SetOverlayAlpha(150.0)
	buffers = segmentationBuffers(net = segmentationNet, stats = "store_true", visualize = "overlay")

def automaticTrackingSlot(activeTrackingFlag, activeTrackingToggle, servoSlider1, servoSlider2, statusLabel):
	if activeTrackingToggle.isToggled():
		activeTrackingFlag = True
		servoSlider1.setEnabled(False)
		servoSlider2.setEnabled(False)		
		print("\033[33;48m[INFO]\033[m   Active target tracking On")
		statusLabel.setText("Active target tracking enabled")
	else:
		activeTrackingFlag = False
		servoSlider1.setEnabled(True)
		servoSlider2.setEnabled(True)		
		statusLabel.setText("No feature selected")
		print("\033[33;48m[INFO]\033[m   Active target tracking Off")

def manualSelectionSlot(loadTrackingModelFlag, manualSelectionToggle, statusLabel):
	if manualSelectionToggle.isToggled():
		print("\033[33;48m[INFO]\033[m   Manual Detection On")
		loadTrackingModelFlag = True
		statusLabel.setText("Tracking Algorithm - CSRT")
		print("\033[33;48m[INFO]\033[m   Object Detection On")
	else:
		statusLabel.setText("No feature selected")
		loadTrackingModelFlag = False
		print("\033[33;48m[INFO]\033[m   Manual Detection Off")

def objectDetectionSlot(loadDetectionModelFlag, objectDetectionToggle, statusLabel, detectionNet):
	if objectDetectionToggle.isToggled():
		loadDetectionModelFlag = True
		statusLabel.setText("Detection Model - SSD-MobileNet-V2\nTrained on {} clases".format(detectionNet.GetNumClasses()))
		print("\033[33;48m[INFO]\033[m   Object Detection On")
	else:
		statusLabel.setText("No feature selected")
		loadDetectionModelFlag = False
		print("\033[33;48m[INFO]\033[m   Object Detection Off")

def objectSegmentationSlot(loadSegmentationModelFlag, objectSegmentationToggle, statusLabel):
	global loadSegmentationModelSignal
	if objectSegmentationToggle.isToggled():
		loadSegmentationModelFlag = True
		loadSegmentationModelSignal -= 1
		statusLabel.setText("Detection Model - FCN-ResNet18-VOC\nTrained on {} clases".format(segmentationNet.GetNumClasses()))
		print("\033[33;48m[INFO]\033[m   Object Segmentation On")
	else:
		statusLabel.setText("No feature selected")
		print("\033[33;48m[INFO]\033[m   Object Segmentation Off")
		loadSegmentationModelFlag = False
		loadSegmentationModelSignal += 1

# Create main window
class MainWindow(QWidget):
	def __init__(self):
		super(MainWindow, self).__init__()
		self.initUI()

	def initUI(self):
		"""
		Initialize window geometry. Render the window at the center of the screen.
		"""
		qtRectangle = self.frameGeometry()
		centerPoint = QDesktopWidget().availableGeometry().center()
		qtRectangle.moveCenter(centerPoint)
		self.move(qtRectangle.topLeft())

		# Size, Title & Background Config
		self.setFixedWidth(1000)
		self.setFixedHeight(430)
		self.setStyleSheet("background-color: rgb(52, 23, 72);")
		self.setWindowTitle("MOS - Mechatronic Orientation System")

		# Config Layout
		self.HBL1 = QHBoxLayout()
		self.HBL2 = QHBoxLayout()
		self.HBL3 = QHBoxLayout()
		self.HBL4 = QHBoxLayout()
		self.HBL5 = QHBoxLayout()
		self.grid = QGridLayout()
		self.VBL1 = QVBoxLayout()
		self.VBL2 = QVBoxLayout()
		self.VBL3 = QVBoxLayout()
		self.VBL4 = QVBoxLayout()
		self.VBL5 = QVBoxLayout()
		self.VBL6 = QVBoxLayout()
		self.VBL7 = QVBoxLayout()
			
		# Stream Label Width & Height
		width = 620
		height = 480

		# Instantiate Additional Thread for Video Stream
		self.Worker1 = Worker1()
		
		# Stream Placeholder
		self.NoStreamLabel = QLabel()
		self.NoStreamLabel.setGeometry(0, 0, width, height)
		self.NoStreamLabel.setPixmap(QPixmap("Data/no-stream.jpg").scaled(width, height, Qt.KeepAspectRatio))
		self.HBL1.addWidget(self.NoStreamLabel)

		# Create and add Stream Widget to window
		self.FeedLabel = QLabel()
		self.HBL1.addWidget(self.FeedLabel)
			
		# Config & Add buttons 
		# TODO Keep the window geometry and elements fixed while the video streaming is loading after the Start button is pressed
		# TODO Add loading widget between Start button push and loading of the stream
		# Start Button
		self.StartBTN = QPushButton("Start")
		self.StartBTN.setStyleSheet("color: white;")
		self.StartBTN.clicked.connect(self.StartFeed)
		self.StartBTN.setToolTip("Start Video Stream")
		self.StartBTN.setFixedSize(QSize(170,30))
		self.HBL2.addWidget(self.StartBTN)

		# Stop Button
		self.StopBTN = QPushButton("Stop")
		self.StopBTN.setStyleSheet("color: white;")
		self.StopBTN.clicked.connect(self.CancelFeed)
		self.StopBTN.setToolTip("Stop Video Stream")
		self.StopBTN.setFixedSize(QSize(170,30))
		self.HBL2.addWidget(self.StopBTN)

		# Snapshot button
		self.SnapshotBTN = QPushButton("Take Picture")
		self.SnapshotBTN.setStyleSheet("color: white;")
		self.SnapshotBTN.clicked.connect(self.Snapshot)
		self.SnapshotBTN.setToolTip("Snapshot")
		self.SnapshotBTN.setFixedSize(QSize(170,30))
		self.HBL2.addWidget(self.SnapshotBTN)

		# Servo Control Sliders
		# Slider 1 Value Line
		self.labelServo1 = QLabel("Vertical Pan Servo Control")
		self.labelServo1.setStyleSheet("color: rgb(255, 255, 255); font-size: 15px;")
		self.VBL3.addWidget(self.labelServo1)
		
		# Slider 1 - Pan
		self.sliderServo1 = QSlider(Qt.Horizontal)
		self.sliderServo1.setStyleSheet("color: rgb(255, 255, 255);")
		self.sliderServo1.setMinimum(0)
		self.sliderServo1.setMaximum(180)
		self.sliderServo1.setValue(90)
		self.sliderServo1.setTickPosition(QSlider.TicksBelow)
		self.sliderServo1.setTickInterval(18)
		self.sliderServo1.setSingleStep(2)
		self.sliderServo1.setToolTip("Pan Servo Control")
		self.servo1Line = QLineEdit()
		self.servo1Line.setFixedWidth(50)
		self.servo1Line.setStyleSheet("color: black")
		self.servo1Line.setStyleSheet("background-color: rgb(255, 255, 255)")
		self.servo1Line.setText(str(self.sliderServo1.value()))
		self.HBL3.addWidget(self.servo1Line)        
		self.HBL3.addWidget(self.sliderServo1)
		self.HBL3.setSpacing(30)
		self.VBL3.addLayout(self.HBL3)
		self.VBL3.setSpacing(10)

		# Display slider1 value & modify servo angle
		self.sliderServo1.valueChanged.connect(lambda:MoveServo(panMotor, self.sliderServo1.value(), self.sliderServo1, self.servo1Line))
		
		# Slider 2 Value Line
		self.labelServo2 = QLabel("Horizontal Tilt Servo Control")
		self.labelServo2.setStyleSheet("color: rgb(255, 255, 255); font-size: 15px;")
		self.VBL4.addWidget(self.labelServo2)

		# Slider 2 - Tilt
		self.sliderServo2 = QSlider(Qt.Horizontal)
		self.sliderServo2.setStyleSheet("color: rgb(255, 255, 255);")
		self.sliderServo2.setMinimum(0)
		self.sliderServo2.setMaximum(180)
		self.sliderServo2.setValue(90)
		self.sliderServo2.setTickPosition(QSlider.TicksBelow)
		self.sliderServo2.setTickInterval(18)
		self.sliderServo2.setSingleStep(2)
		self.sliderServo2.setToolTip("Tilt Servo Control")
		self.servo2Line = QLineEdit()
		self.servo2Line.setFixedWidth(50)
		self.servo2Line.setStyleSheet("color: black")
		self.servo2Line.setStyleSheet("background-color: rgb(255, 255, 255)")
		self.servo2Line.setText(str(self.sliderServo2.value()))
		self.HBL4.addWidget(self.servo2Line)        
		self.HBL4.addWidget(self.sliderServo2)
		self.HBL4.setSpacing(30)
		self.VBL4.addLayout(self.HBL4)
		self.VBL4.setSpacing(10)

		# Display slider2 value & modify servo angle
		self.sliderServo2.valueChanged.connect(lambda:MoveServo(tiltMotor, self.sliderServo2.value(), self.sliderServo2, self.servo2Line))

		# Toggle for activating/deactivating manual target tracking feature
		self.automaticTrackingToggle = ToggleSwitch(style="ios")

		self.automaticTrackingToggle.toggled.connect(lambda:automaticTrackingSlot(automaticTracking, self.automaticTrackingToggle, self.sliderServo1, self.sliderServo2, self.statusLabel))
		self.automaticTrackingLabel = QLabel("Active Target Tracking")
		self.automaticTrackingLabel.setStyleSheet("color: white; font-size: 15px")
		self.grid.addWidget(self.automaticTrackingLabel, 0, 0)
		self.grid.addWidget(self.automaticTrackingToggle, 0, 1)

		# Toggle for activating/deactivating manual target selection feature
		self.manualSelectionToggle = ToggleSwitch(style="ios")

		self.manualSelectionToggle.toggled.connect(lambda:manualSelectionSlot(loadTrackingModel, self.manualSelectionToggle, self.statusLabel))
		self.manualSelectionToggleLabel = QLabel("Manual Target Detection")
		self.manualSelectionToggleLabel.setStyleSheet("color: white; font-size: 15px")
		self.grid.addWidget(self.manualSelectionToggleLabel, 1, 0)
		self.grid.addWidget(self.manualSelectionToggle, 1, 1)

		# Toggle for activating/deactivating object detection feature
		self.objectDetectionToggle = ToggleSwitch(text="", style="ios")

		self.objectDetectionToggle.toggled.connect(objectDetectionSlot)
		self.objectDetectionToggleLabel = QLabel("Automatic Target Detection", self)
		self.objectDetectionToggleLabel.setStyleSheet("color: white; font-size: 15px")
		self.grid.addWidget(self.objectDetectionToggleLabel, 2, 0)
		self.grid.addWidget(self.objectDetectionToggle, 2, 1)

		# Toggle for activating/deactivating object segmentation feature
		self.objectSegmentationToggle = ToggleSwitch(text="", style="ios")
		self.objectSegmentationToggle.toggled.connect(lambda:objectSegmentationSlot(loadSegmentationModel, self.objectSegmentationToggle, self.statusLabel))
		self.objectSegmentationToggleLabel = QLabel("Automatic Target Segmentation")
		self.objectSegmentationToggleLabel.setStyleSheet("color: white; font-size: 15px")
		self.grid.addWidget(self.objectSegmentationToggleLabel, 3, 0)
		self.grid.addWidget(self.objectSegmentationToggle, 3, 1)
		self.grid.setContentsMargins(0, 30, 30, 0)
		self.VBL5.addLayout(self.grid)

		# Separator Line
		self.line = QFrame()
		self.line.setGeometry(QRect(630, 400, 25, 25))
		self.line.setFrameShape(QFrame.HLine)
		self.line.setFrameShadow(QFrame.Sunken)
		self.VBL5.addWidget(self.line)

		# Status Label
		self.statusLabel = QLabel("No feature selected")
		self.statusLabel.setStyleSheet("color: white; font-size: 15px")
		self.VBL5.addWidget(self.statusLabel)
		
		# Combine horizontal and vertical layout
		# 1) Vertially Stack Feed_Label and Pushbuttons
		self.VBL1.addLayout(self.HBL1)
		self.VBL1.addLayout(self.HBL2)

		# 2) Vertically Stack servo control sliders and toggles
		self.VBL7.addLayout(self.VBL3)
		self.VBL7.addLayout(self.VBL4)
		self.VBL7.setSpacing(30)
		self.VBL6.addLayout(self.VBL7)
		self.VBL2.addLayout(self.VBL6)
		self.VBL2.addLayout(self.VBL5)
		self.VBL2.addStretch()

		# Horizontally Stack (1) and (2)
		self.HBL5.addLayout(self.VBL1)
		self.HBL5.addLayout(self.VBL2)    
	
		self.Worker1.ImageUpdate.connect(self.ImageUpdate)
		self.setLayout(self.HBL5)

	def StartFeed(self):
		"""
		Define behavior for start button. Change video stream label content and start video streaming thread.
		"""
		self.NoStreamLabel.setHidden(True)
		self.FeedLabel.setHidden(False)
		self.Worker1.start()
		print("\033[33;48m[INFO]\033[m   Start button pressed")

	def ImageUpdate(self, Image):
		"""Update content of the video streaming label in the user interface.

		Args:
			Image (QImage): Image to update label content with
		"""
		self.FeedLabel.setPixmap(QPixmap.fromImage(Image))

	def CancelFeed(self):
		"""
		Define behavior for stop button. Change video stream label content and stop video streaming thread.
		"""
		self.Worker1.exit()
		self.FeedLabel.setHidden(True)
		self.NoStreamLabel.setHidden(False)
		print("\033[33;48m[INFO]\033[m   Stop button pressed")

	def Snapshot(self):
		"""
		Record current content of the video stream label and store it locally.

		"""
		self.FeedLabel.pixmap().save("./Data/Images/test.jpg")
		print("\033[33;48m[INFO]\033[m   Snapshot button pressed")


class Worker1(QThread):
	"""Worker thread aimed to handle the video stream related tasks. Frame capturing and video processing baesd on user control.

	Args:
		QThread (QThread): Inherit from class QThread
	"""
	ImageUpdate = pyqtSignal(QImage)

	def run(self):
		"""
		Handle thread responssible actions for video control and processing.
		Invoke this method whenever a instance of the class is created.
		"""
		self.ThreadActive = True
		trackerInitialized = False
		if self.started:
			global loadTrackingModel, loadDetectionModel, detectionNet, loadSegmentationModel, segmentationNet, automaticTracking, tracker
			self.pipelineSetUp()
			prevFrameTime = 0

			def drawRectangleFromBbox(frame, bbox, centerFlag):
				"""Draw rectangle on a frame to highligh selection position and size.
				Use the centerFlag parameter to control the visibility of the selection center display status.

				Args:
					frame (cvMat): Frame to draw onto
					bbox (list): Selection bounding box instance
					centerFlag (bool): Flag to control whether the selection cetner is displayed or not
				"""
				x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
				cv.rectangle(frame, (x,y), (x+w,y+h), (0,0,255), 2)
				if centerFlag:
					cv.circle(frame, (x+(w)//2, y+(h)//2 ), 30, (0, 255, 255), -1)
				cv.putText(frame, "Tracking", (7, 150), cv.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)

			while self.ThreadActive:
				frame = self.camera.Capture()
				if loadDetectionModel and type(detectionNet) != None:
					detections = detectionNet.Detect(frame)
					for detection in detections:
						if detection.ClassID == 1:
							xTarget, yTarget = detection.Center
							FollowTarget(panMotor, tiltMotor, xTarget, yTarget, self.size[0], self.size[1], automaticTracking)
							print("\033[32;48m[FOUND]\033[m   Person detected at: {}, {}".format(xTarget, yTarget))

				if loadSegmentationModel:
					# TODO Automatically close segmentation window when segmentation toggle is turned off
					buffers.Alloc(frame.shape, frame.format)
					segmentationNet.Process(frame, ignore_class="void")
					segmentationNet.Overlay(buffers.overlay, filter_mode="point")
					jetson.utils.cudaOverlay(buffers.overlay, buffers.overlay, 0, 0)
					self.display.Render(buffers.output)
				else:
					if loadSegmentationModelSignal % 2 != 0:
						self.display.Close()
						# del self.display
						
				jetson.utils.cudaDeviceSynchronize()
				frame = jetson.utils.cudaToNumpy(frame, frame.width, frame.height, 4)
				
				if loadTrackingModel:
					if not trackerInitialized:
						bbox = cv.selectROI(frame, False)
						tracker.init(frame, bbox)
					trackerInitialized = True
					cv.destroyWindow("ROI selector")
					retVal, bbox = tracker.update(frame)
					FollowTarget(panMotor, tiltMotor, bbox[0] + bbox[2]//2, bbox[1] + bbox[3]//2, self.size[0], self.size[1], automaticTracking)
					print("\033[32;48m[FOUND]\033[m   Target center selected at: {}, {}".format(bbox[0]+(bbox[2]-bbox[0])/2, bbox[1] + (bbox[3]-bbox[1])/2))
					if retVal:
						drawRectangleFromBbox(frame, bbox, True)
					else:
						cv.putText(frame, "Target Lost", (7, 150), cv.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)
				
				if np.sum(frame) != 0:
					newFrameTime = time.time()
					FPS = "FPS: " + str(int(1/(newFrameTime - prevFrameTime)))
					prevFrameTime = newFrameTime
					cv.putText(frame, FPS, (7, 70), cv.FONT_HERSHEY_SIMPLEX, 2, (100, 255, 0), 2)
					cv.circle(frame, (self.frameCenter[0], self.frameCenter[1]), 50, (0, 255, 255), -1)
					Convert2QtFormat = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
					Pic = Convert2QtFormat.scaled(620, 480, Qt.KeepAspectRatio)
					self.ImageUpdate.emit(Pic)
				else:
					print("\033[31;48m[DEBUG]\033[m  Error while reading frame. Cannot load empty frame. Exist Status -1.")
				# print("\033[31;48m[DEBUG]\033[m  Frame center at", self.frameCenter)
		else:
			print("\033[31;48m[DEBUG]\033[m  Image processing thread has stopped. Exit status -2.")

	def pipelineSetUp(self):
		"""
		Setup video streaming pipeline with appropriate arguments
		"""
		camera = jetson.utils.videoSource("csi://0", argv=["--input-flip=rotate-180"])
		self.camera = camera
		self.size = [camera.GetWidth(), camera.GetHeight()]
		self.frameCenter = [self.size[0]//2, self.size[1]//2]
		display = jetson.utils.videoOutput("display://0")
		self.display = display

	def stop(self):
		"""
		Kill current video streaming session
		"""
		self.ThreadActive = False
		if self.isRunning():
			self.quit()

class Worker2(QThread):
	"""Worker thread aimed to load the application session dependent parameters.

	Args:
		QThread (QThread): Inheritance from QThread class
	"""
	def run(self):
		"""Handle thread responssible actions for tracking, detection and semantic segmentation model loading.
		Invoke this method whenever a instance of the class is created.
		"""
		loadModels()


if __name__ == '__main__':
	App = QApplication(sys.argv)
	App.setWindowIcon(QIcon("Data/favicon.png"))
	splashImg = QPixmap("Data/logo.png")
	splashImg = splashImg.scaled(640, 480, Qt.KeepAspectRatio)
	splashScreen = QSplashScreen(splashImg, Qt.WindowStaysOnTopHint)
	splashScreen.show()
	App.processEvents()
	modelsThread = Worker2()
	modelsThread.run()
	MOSapp = MainWindow()
	splashScreen.finish(MOSapp)
	MOSapp.show()
	sys.exit(App.exec())