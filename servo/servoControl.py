def FollowTarget(panServo, tiltServo, xTarget, yTarget, frameWidth, frameHeight, errCoeff = 70, enableFlag = True):
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
    panErr = xTarget - frameWidth/2
    tiltErr = yTarget - frameHeight/2
    if enableFlag:
        # Control servo position based on target position
        if abs(panErr) > 15:
            panServo = panServo.angle - panErr/errCoeff
        if abs(tiltErr) > 15:
            tiltServo = tiltServo.angle - tiltErr/errCoeff
        
        # Define range limit behavior
        if panServo.angle > 180:
            panServo.angle = 180
        if tiltServo.angle > 180:
            tiltServo = 180
    else:
        print("\033[31;48m[DEBUG]\033[m  Active tracking spawned but disabled")