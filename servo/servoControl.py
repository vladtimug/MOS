def followTarget(panServo, tiltServo, xFrameCenter, yFrameCenter, xTarget, yTarget, enableFlag):
    if enableFlag:
        if xTarget > xFrameCenter + 15:		# act on pan servo
            panServo.angle -= 1
        elif xTarget < xFrameCenter - 15:
            panServo.angle += 1
        if yTarget <  yFrameCenter - 10:		# act on tilt servo
            tiltServo.angle -= 1
        elif yTarget >  yFrameCenter + 10:
            tiltServo.angle += 1
    else:
        print("\033[31;48m[DEBUG]\033[m  Active tracking spawned but disabled")