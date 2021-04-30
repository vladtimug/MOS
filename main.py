import cv2 as cv

def gstreamer_pipeline(
    capture_width=1280,
    capture_height=720,
    display_width=680,
    display_height=460,
    framerate=20,
    flip_method=0,
):
    return (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

Capture = cv.VideoCapture(gstreamer_pipeline(flip_method=0), cv.CAP_GSTREAMER)

if Capture.isOpened():
    while True:
        _, frame = Capture.read()

        cv.imshow("stream", frame)

        if cv.waitKey(1) == 27:
            break
Capture.release()
cv.destroyAllWindows()