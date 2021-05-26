#!/usr/bin/python3
# Threads: https://www.youtube.com/watch?v=dTDgbx-XelY

import sys

from colorama.ansi import Style
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import cv2 as cv
# from adafruit_servokit import ServoKit
import numpy as np
import jetson.inference
import jetson.utils
from segnet_utils import *
from pyqt5Custom import ToggleSwitch

import time

# Servo setup
# myKit = ServoKit(channels = 16)
# tiltMotor = myKit.servo[14]		# Tilt motor
# panMotor = myKit.servo[15]		# Pan motor

loadTrackingModel = False
loadDetectionModel = False
loadSegmentationModel = False

output = jetson.utils.videoOutput()

tracker = cv.TrackerCSRT_create()
detectionNet = jetson.inference.detectNet("ssd-mobilenet-v2", threshold = 0.5)
segmentationNet = jetson.inference.segNet("fcn-resnet18-voc")
segmentationNet.SetOverlayAlpha(150.0)
buffers = segmentationBuffers(net = segmentationNet, stats = "store_true", visualize = "overlay")

# Create main window
class MainWindow(QWidget):
	def __init__(self):
		# Inherit from QWidget Obj. Super returns the parrent object -> in this case a Qwidget obj
			super(MainWindow, self).__init__()
			self.initUI()

	def initUI(self):
		# Size, Title & Background Config
			self.setFixedWidth(1000)
			self.setFixedHeight(430)
			self.setStyleSheet("background-color: rgb(52, 23, 72);")
			self.setWindowTitle("MOS")

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
			self.NoStreamLabel.setPixmap(QPixmap("no-stream.jpg").scaled(width, height, Qt.KeepAspectRatio))
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
			self.labelServo1 = QLabel("Horizontal Pan Servo Control")
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
			# self.sliderServo1.valueChanged.connect(self.v_change_servo1)
			
			# Slider 2 Value Line
			self.labelServo2 = QLabel("Vertical Tilt Servo Control")
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
			# self.sliderServo2.valueChanged.connect(self.v_change_servo2)

		# Toggle for activating/deactivating manual target selection feature
			self.manualSelectionToggle = ToggleSwitch(style="ios")
			def manualSelectionSlot():
				global loadTrackingModel
				if self.manualSelectionToggle.isToggled():
					print("\033[33;48m[INFO]\033[m   Manual Detection On")
					loadTrackingModel = True
					
				else:
					print("\033[33;48m[INFO]\033[m   Manual Detection Off")
					loadTrackingModel = False

			self.manualSelectionToggle.toggled.connect(manualSelectionSlot)
			self.manualSelectionToggleLabel = QLabel("Manual Target Detection")
			self.manualSelectionToggleLabel.setStyleSheet("color: white; font-size: 15px")
			self.grid.addWidget(self.manualSelectionToggleLabel, 0, 0)
			self.grid.addWidget(self.manualSelectionToggle, 0, 1)

		# Toggle for activating/deactivating object detection feature
			self.objectDetectionToggle = ToggleSwitch(text="", style="ios")
			def objectDetectionSlot():
				global loadDetectionModel
				if self.objectDetectionToggle.isToggled():
					loadDetectionModel = True
					print("\033[33;48m[INFO]\033[m   Object Detection On")
				else:
					loadDetectionModel = False
					print("\033[33;48m[INFO]\033[m   Object Detection Off")

			self.objectDetectionToggle.toggled.connect(objectDetectionSlot)
			self.objectDetectionToggleLabel = QLabel("Automatic Target Detection")
			self.objectDetectionToggleLabel.setStyleSheet("color: white; font-size: 15px")
			self.grid.addWidget(self.objectDetectionToggleLabel, 1, 0)
			self.grid.addWidget(self.objectDetectionToggle, 1, 1)

		# Toggle for activating/deactivating object segmentation feature
			self.objectSegmentationToggle = ToggleSwitch(text="", style="ios")
			def objectSegmentationSlot():
				global loadSegmentationModel
				if self.objectSegmentationToggle.isToggled():
					print("\033[33;48m[INFO]\033[m   Object Segmentation On")
					loadSegmentationModel = True
				else:
					print("\033[33;48m[INFO]\033[m   Object Segmentation Off")
					loadSegmentationModel = False
			self.objectSegmentationToggle.toggled.connect(objectSegmentationSlot)
			self.objectSegmentationToggleLabel = QLabel("Automatic Target Segmentation")
			self.objectSegmentationToggleLabel.setStyleSheet("color: white; font-size: 15px")
			self.grid.addWidget(self.objectSegmentationToggleLabel, 2, 0)
			self.grid.addWidget(self.objectSegmentationToggle, 2, 1)
			self.grid.setContentsMargins(0, 30, 30, 0)
			self.VBL5.addLayout(self.grid) 

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
		self.NoStreamLabel.setHidden(True)
		self.FeedLabel.setHidden(False)
		self.Worker1.start()
		print("\033[33;48m[INFO]\033[m   Start button pressed")

	def ImageUpdate(self, Image):
		self.FeedLabel.setPixmap(QPixmap.fromImage(Image))

	def CancelFeed(self):   
		self.Worker1.exit()
		self.FeedLabel.setHidden(True)
		self.NoStreamLabel.setHidden(False)
		print("\033[33;48m[INFO]\033[m   Stop button pressed")

	def Snapshot(self, Image):
		self.FeedLabel.pixmap().save("./Data/Images/test.jpg")
		print("\033[33;48m[INFO]\033[m   Snapshot button pressed")

	def v_change_servo1(self):
		current_value = str(self.servo1.value())
		self.servo1_line.setText(current_value)
		panMotor.angle = self.servo1.value()

	def v_change_servo2(self):
		current_value = str(self.servo2.value())
		self.servo2_line.setText(current_value)
		tiltMotor.angle = self.servo2.value()

class Worker1(QThread):
	ImageUpdate = pyqtSignal(QImage)

	def run(self):
		self.ThreadActive = True
		if self.started:
			# global output
			global loadTrackingModel
			global loadDetectionModel
			global detectionNet
			global loadSegmentationModel
			global segmentationNet
			self.pipelineSetUp()
			prevFrameTime = 0

			if loadTrackingModel:
				# TODO Implement reselection of the object to track when the target is lost or
				# TODO run object detector when target is lost (it has to be the same object)
				global tracker
				def drawRectangleFromBbox(frame, bbox):
					x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
					cv.rectangle(frame, (x,y), (x+w,y+h), (0,0,255), 2)
					cv.putText(frame, "Tracking", (7, 150), cv.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)
				frame = self.camera.Capture()
				frame = jetson.utils.cudaToNumpy(frame, frame.width, frame.height, 4)
				
				# frame = cv.cvtColor("Live Stream", frame, cv.COLOR_BGR2RGB)
				bbox = cv.selectROI(frame, False)
				# input("Select ROI and press Enter to continue")
				tracker.init(frame, bbox)
				cv.destroyWindow("ROI selector")

			while self.ThreadActive and self.display.IsStreaming():
				frame = self.camera.Capture()
				if loadDetectionModel and type(detectionNet) != None:
					detections = detectionNet.Detect(frame)

				if loadSegmentationModel and type(segmentationNet) != None:
					buffers.Alloc(frame.shape, frame.format)
					segmentationNet.Process(frame, ignore_class="void")
					segmentationNet.Overlay(buffers.overlay, filter_mode="linear")
					jetson.utils.cudaOverlay(buffers.overlay, buffers.overlay, 0, 0)
					self.display.Render(buffers.output)

				jetson.utils.cudaDeviceSynchronize()
				frame = jetson.utils.cudaToNumpy(frame, frame.width, frame.height, 4)
				
				if loadTrackingModel:
					retVal, bbox = tracker.update(frame)
					if retVal:
						drawRectangleFromBbox(frame, bbox)
					else:
						cv.putText(frame, "Target Lost", (7, 150), cv.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)
					# cv.destroyAllWindows()
				
				if np.sum(frame) != 0:
					newFrameTime = time.time()
					FPS = "FPS: " + str(int(1/(newFrameTime - prevFrameTime)))
					prevFrameTime = newFrameTime
					cv.putText(frame, FPS, (7, 70), cv.FONT_HERSHEY_SIMPLEX, 2, (100, 255, 0), 2)
					Convert2QtFormat = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
					Pic = Convert2QtFormat.scaled(620, 480, Qt.KeepAspectRatio)
					self.ImageUpdate.emit(Pic)
				else:
					print("\033[31;48m[DEBUG]\033[m  Error while reading frame. Cannot load empty frame. Exist Status -1.")
		else:
			print("\033[31;48m[DEBUG]\033[m  Image processing thread has stopped. Exit status -2.")

	def pipelineSetUp(self):
		camera = jetson.utils.videoSource("csi://0", argv=["--input-flip=rotate-180"])
		self.camera = camera
		display = jetson.utils.videoOutput("display://0")
		self.display = display

	def stop(self):
		self.ThreadActive = False
		if self.isRunning():
			self.quit()

if __name__ == '__main__':
	App = QApplication(sys.argv)
	Root = MainWindow()
	Root.show()
	sys.exit(App.exec())