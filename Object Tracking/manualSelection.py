# This script tests various methods for object tracking through frames
# A manual selection operation of the target object is needed
import nanocamera as nano
import cv2 as cv
camera = nano.Camera()
# import argparse

# argumentParser = argparse.ArgumentParser()
# argumentParser.add_argument("-t", "--tracker", type=str, default="MOSSE", help="Type of tracker")
# trackerArgs = argumentParser.parse_args()

def drawRectangleFromBbox(frame, bbox):
    x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
    cv.rectangle(frame, (x,y), (x+w,y+h), (0,0,255), 1)
    cv.putText(frame, "Tracking", (50, 70), cv.FONT_HERSHEY_SIMPLEX, .7, (0, 255, 0), 2)

# OPENCV_OBJECT_TRACKERS = {
#     "csrt": cv.TrackerCSRT_create,    ---------------->  Pretty slow not that great
#     "kcf": cv.TrackerKCF_create,      ---------------->  Decent speed, decent accuracy
#     # "boosting": cv.TrackerBoosting_create,
#     "mil": cv.TrackerMIL_create,      ---------------->  Decent speed, decent accuracy
#     # "tld": cv.TrackerTLD_create,
#     # "medianflow": cv.TrackerMedianFlow_create,
#     # "mosse": cv.TrackerMOSSE_create
# }
# cap = cv.VideoCapture(0)
frame= camera.read()
bbox = cv.selectROI("Live Stream", frame, False)

# tracker = OPENCV_OBJECT_TRACKERS[trackerArgs["tracker"]]()
tracker = cv.TrackerKCF_create()
tracker.init(frame, bbox)

while camera.isReady() :
    timer = cv.getTickCount()
    frame= camera.read()

    retVal, bbox = tracker.update(frame)
    
    if retVal:
        drawRectangleFromBbox(frame, bbox)
    else:
        cv.putText(frame, "Target Lost", (50, 70), cv.FONT_HERSHEY_SIMPLEX, .7, (255, 0, 0), 2)
    fps = cv.getTickFrequency()/(cv.getTickCount()-timer)
    cv.putText(frame, "FPS: " + str(int(fps)), (50, 50), cv.FONT_HERSHEY_SIMPLEX, .7, (0, 255, 0), 2)
    cv.imshow("Live Stream", frame)

    if cv.waitKey(1) == 27:
        break

# cap.release()
del camera
cv.destroyAllWindows()