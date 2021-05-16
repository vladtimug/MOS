MOS - Mechatronic Orientation System for Mobile Robots

This app is only the software component of the project.
The second part of the project consist of the hardware as follows:
+ Pan tilt mechanism, either bought or 3d printed
+ Raspberry Pi Module V2 Camera or a usb camera
+ 2 Servos
+ Raspberry Pi, Jetson Nano or other similar computing platform
+ Adafruit servo driver. I used PCA9685.

Running the project
+ Step 1 - Clone this repository
+ Step 2 - Install the dependencies
+ Step 3 - Run the code

To validate communication via I2C
+ Attach the logic power pins and the SCL/SDA pins from the driver to the board
+ Power the driver 
+ Use the following command: i2cdetect -y -r 1
+ Check for a valid positive output message