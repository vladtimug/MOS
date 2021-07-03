def limitPos(servoPosition):
    """Prevent servo position from exceeding limited range

    Args:
        servoPosition (int): Servo angle position in degrees

    Returns:
        (int): Servo position in degrees
    """
    if servoPosition > 180:
        servoPosition = 180
    return servoPosition

def FollowTarget(panServo, tiltServo, xTarget, yTarget, frameWidth, frameHeight, enableFlag, errCoeff = 70):
    """Control tilt and pan axis of the mechanism to actively track objects found at xTarget and yTarget

    Args:
        panServo (ServoKit.servo): Pan servo motor object
        tiltServo (ServoKit.servo): Tilt servo motor object
        xTarget (int): x coordinate fo target to track
        yTarget (int): y coordinate fo target to track
        frameWidth (int): Current frame width
        frameHeight: Current frame height
        errCoeff: Error correction coefficient. 70 by default.
        enableFlag (bool): Control flag for position control. True by default.
    """
    panErr = xTarget - frameWidth//2
    tiltErr = yTarget - frameHeight//2

    if panErr and tiltErr:
        if enableFlag:
            # Control servo position based on target position
            if abs(panErr) > 15:
                panServo.angle = limitPos(panServo.angle - panErr//errCoeff)
            if abs(tiltErr) > 15:
                tiltServo.angle = limitPos(tiltServo.angle - tiltErr//errCoeff)
        else:
            print("\033[31;48m[DEBUG]\033[m  Active tracking spawned but disabled")
    else:
        print("\033[31;48m[DEBUG]\033[m  No error to correct")