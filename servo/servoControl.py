def FollowTarget(panServo, tiltServo, xRefference, yReferrence, xTarget, yTarget, enableFlag):
    """Control tilt and pan axis of the mechanism to actively track objects found at xTarget and yTarget

    Args:
        panServo (ServoKit.servo): Pan servo motor object
        tiltServo (ServoKit.servo): Tilt servo motor object
        xRefference (int): x coordinate refference position
        yReferrence (int): y coordinate refference position
        xTarget (int): x coordinate fo target to track
        yTarget (int): y coordinate fo target to track
        enableFlag (bool): Control flag for position control
    """
    if enableFlag:
        if xTarget > xRefference + 15:		# act on pan servo
            panServo.angle -= 1
        elif xTarget < xRefference - 15:
            panServo.angle += 1
        if yTarget <  yReferrence - 10:		# act on tilt servo
            tiltServo.angle -= 1
        elif yTarget >  yReferrence + 10:
            tiltServo.angle += 1
    else:
        print("\033[31;48m[DEBUG]\033[m  Active tracking spawned but disabled")