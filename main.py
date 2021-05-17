# Threads: https://www.youtube.com/watch?v=dTDgbx-XelY

import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import cv2 as cv
# from adafruit_servokit import ServoKit
# import nanocamera as nano
import numpy as np
import jetson.inference
import jetson.utils

# Servo setup
# myKit = ServoKit(channels = 16)
# tiltMotor = myKit.servo[14]		# Tilt motor
# panMotor = myKit.servo[15]		# Pan motor

# Create main window
# TODO Check out https://github.com/kadir014/pyqt5-custom-widgets to enhance UI
class MainWindow(QWidget):
    def __init__(self):
        # Inherit from QWidget Obj. Super returns the parrent object -> in this case a Qwidget obj
            super(MainWindow, self).__init__()

        # Size, Title & Background Config
            self.setFixedWidth(1000)
            self.setFixedHeight(500)
            self.setStyleSheet("background-color: rgb(150,97,97);")
            self.setWindowTitle("MESS")

        # Config Layout
            self.HBL1 = QHBoxLayout()
            self.HBL2 = QHBoxLayout()
            self.HBL3 = QHBoxLayout()
            self.HBL4 = QHBoxLayout()
            self.HBL5 = QHBoxLayout()
            self.HBL6 = QHBoxLayout()
            self.VBL1 = QVBoxLayout()
            self.VBL2 = QVBoxLayout()
            self.VBL3 = QVBoxLayout()
            self.VBL4 = QVBoxLayout()
            
        # Stream Width & Height
            width = 620
            height = 480

        # Instantiate & Start Additional Thread for Video Stream
            self.Worker1 = Worker1()
        
        # Stream Placeholder
            self.NoStreamLabel = QLabel()
            self.NoStreamLabel.setPixmap(QPixmap("no-stream.jpg").scaled(width, height, Qt.KeepAspectRatio))
            self.HBL1.addWidget(self.NoStreamLabel)

        # Create and add Stream Widget to window
            self.FeedLabel = QLabel()
            # self.FeedLabel.setFixedHeight(859)
            # self.FeedLabel.setFixedWidth(480)
            # self.FeedLabel.setGeometry(QRect(0, 0, 720, 480))
            self.HBL1.addWidget(self.FeedLabel)
            
        # Config & Add buttons 
            # Start Button
            self.StartBTN = QPushButton("Start")
            self.StartBTN.setStyleSheet("color: white;")
            self.StartBTN.clicked.connect(self.StartFeed)
            self.StartBTN.setToolTip("Start Video Stream")
            self.StartBTN.setFixedSize(QSize(230,30))
            self.HBL2.addWidget(self.StartBTN)

            # Stop Button
            self.StopBTN = QPushButton("Stop")
            self.StopBTN.setStyleSheet("color: white;")
            self.StopBTN.clicked.connect(self.CancelFeed)
            self.StopBTN.setToolTip("Stop Video Stream")
            self.StopBTN.setFixedSize(QSize(230,30))
            self.HBL2.addWidget(self.StopBTN)

            # Snapshot button
            self.SnapshotBTN = QPushButton("Take Picture")
            self.SnapshotBTN.setStyleSheet("color: white;")
            self.SnapshotBTN.clicked.connect(self.CancelFeed)
            self.SnapshotBTN.setToolTip("Snapshot")
            self.SnapshotBTN.setFixedSize(QSize(230,30))
            self.HBL2.addWidget(self.SnapshotBTN)
            
            # Manual Selection button
            self.manSelect = QPushButton("Manual Selection", self)
            self.manSelect.setCheckable(True)
            # self.manSelect.setStyleSheet("background-color: lightgrey")
            self.SnapshotBTN.setFixedSize(QSize(150,30))
            self.manSelect.clicked.connect(self.changeColor)
            self.HBL6.addWidget(self.manSelect)

        # Servo Control Sliders
            # Slider 1 - Pan
            self.label_servo1 = QLabel("Pan Servo Control")
            self.label_servo1.setStyleSheet("color: white")
            self.servo1 = QSlider(Qt.Horizontal)
            self.servo1.setMinimum(0)
            self.servo1.setMaximum(180)
            self.servo1.setValue(90)
            self.servo1.setTickPosition(QSlider.TicksBelow)
            self.servo1.setTickInterval(18)
            self.servo1.setToolTip("Pan Servo Control")
            self.HBL3.addWidget(self.label_servo1)        
            self.HBL3.addWidget(self.servo1)

            # Slider 1 Value Line
            self.servo1_line = QLineEdit()
            self.servo1_line.setFixedWidth(50)
            self.servo1_line.setStyleSheet("color: black")
            self.servo1_line.setStyleSheet("background-color: rgb(0, 179, 255)")
            self.servo1_line.setText(str(self.servo1.value()))
            self.VBL3.addWidget(self.servo1_line)

        # Display slider1 value & modify servo angle
            # self.servo1.valueChanged.connect(self.v_change_servo1)
            
        # Slider 2 - Tilt
            self.label_servo2 = QLabel("Tilt Servo Control")
            self.label_servo2.setStyleSheet("color: white")
            self.servo2 = QSlider(Qt.Horizontal)
            self.servo2.setMinimum(0)
            self.servo2.setMaximum(180)
            self.servo2.setValue(90)
            self.servo2.setTickPosition(QSlider.TicksBelow)
            self.servo2.setTickInterval(18)
            self.servo2.setToolTip("Tilt Servo Control")
            self.HBL4.addWidget(self.label_servo2)        
            self.HBL4.addWidget(self.servo2)

        # Slider 2 Value Line
            self.servo2_line = QLineEdit()
            self.servo2_line.setFixedWidth(50)
            self.servo2_line.setStyleSheet("color: black")
            self.servo2_line.setStyleSheet("background-color: rgb(0, 179, 255)")
            self.servo2_line.setText(str(self.servo2.value()))
            self.VBL4.addWidget(self.servo2_line)
        
        # Display slider2 value & modify servo angle
            # self.servo2.valueChanged.connect(self.v_change_servo2)

        # Combine horizontal and vertical layout
            # 1) Vertially Stack Feed_Label and Pushbuttons
            self.VBL1.addLayout(self.HBL1)
            self.VBL1.addLayout(self.HBL2)

            # 2) Vertically Stack servo control sliders 
            self.VBL2.addLayout(self.HBL3)
            self.VBL2.addLayout(self.VBL3)
            self.VBL2.addLayout(self.HBL4)
            self.VBL2.addLayout(self.VBL4)
            self.VBL2.addLayout(self.HBL6)
            self.VBL2.addStretch()
            # Manual selection toggle

            # Horizontally Stack (1) and (2)
            self.HBL5.addLayout(self.VBL1)
            self.HBL5.addLayout(self.VBL2)    
        
            self.Worker1.ImageUpdate.connect(self.ImageUpdateSlot)
            self.setLayout(self.HBL5)

    def StartFeed(self):
        self.Worker1.start()
        self.NoStreamLabel.setHidden(True)
        self.FeedLabel.setHidden(False)

    def ImageUpdateSlot(self, Image):
        self.FeedLabel.setPixmap(QPixmap.fromImage(Image))

    def CancelFeed(self):
        self.Worker1.stop()
        self.FeedLabel.setHidden(True)
        self.NoStreamLabel.setHidden(False)

    def SnapShoot(self):
        pass

    def v_change_servo1(self):
        current_value = str(self.servo1.value())
        self.servo1_line.setText(current_value)
        panMotor.angle = self.servo1.value()

    def v_change_servo2(self):
        current_value = str(self.servo2.value())
        self.servo2_line.setText(current_value)
        tiltMotor.angle = self.servo2.value()

    def changeColor(self):
        if self.manSelect.isChecked():
            self.manSelect.setStyleSheet("background-color: lightblue")
            cv.namedWindow("CSI Camera", cv.WINDOW_NORMAL)
        else:
            self.manSelect.setStyleSheet("background-color: lightgrey")

# TODO Create similar class for object detection or create different run functions
class Worker1(QThread):
    ImageUpdate = pyqtSignal(QImage)
    def run(self):
        self.ThreadActive = True
        # Capture = nano.Camera()
        # camera = jetson.utils.gstCamera(1280, 720, "0")
        # display = jetson.utils.glDisplay()
        camera = jetson.utils.videoSource("csi://0", argv=["--input-flip=rotate-180"])
        display = jetson.utils.videoOutput("display://0")
        if camera != None:
            while self.ThreadActive and display.IsStreaming():
                frame = camera.Capture()
                # frame0, widht, height = camera.CaptureRGBA(zeroCopy = True)
                # jetson.utils.cudaDeviceSynchronize()
                frame = jetson.utils.cudaToNumpy(frame, frame.width, frame.height, 4)
                if np.sum(frame) != 0:
                    cvFrame = cv.cvtColor(frame.astype(np.uint8), cv.COLOR_BGR2RGB)
                    # FlippedImage = cv.flip(Image, 0)
                    Convert2QtFormat = QImage(cvFrame.data, cvFrame.shape[1], cvFrame.shape[0], QImage.Format_RGB888)
                    Pic = Convert2QtFormat.scaled(620, 480, Qt.KeepAspectRatio)
                    self.ImageUpdate.emit(Pic)
                else:
                    print("Error while reading frame. Cannot load empty frame. Exist Status -1.")
                    self.finished.emit()
        else:
            print("Error opening VideoCapture obj. Exit status -2.")
            self.finished.emit()
    
    def stop(self):
        self.ThreadActive = False
        self.quit()
    
    # def cameraDisplay(self):


if __name__ == '__main__':
    App = QApplication(sys.argv)
    Root = MainWindow()
    Root.show()
    sys.exit(App.exec())