import numpy as np
import argparse 
import time
import cv2 as cv
import os
import nanocamera as nano

argumentsParser = argparse.ArgumentParser()
argumentsParser.add_argument("-g", "--gpu", type=int, default=0, help="Flag to run inference on GPU instead of CPU. 1 - inference on GPU, 0 - inference on CPU. Default is 0.")
argumentsParser.add_argument("-y", "--yolo", required=True, help="Base path to yolo directory")
argumentsParser.add_argument("-c", "--confidence", type=float, default=0.5, help="Minimum probability to filter weak detections")
argumentsParser.add_argument("-t", "--threshold", type=float, default=0.3, help="Threshold when applying non-max suppresion")
arguments = vars(argumentsParser.parse_args())
# print(arguments)

# TODO check for succesfully loaded file using os library
labelsPath = os.path.sep.join([arguments["yolo"], "coco.names"])
print("[INFO] Object classes path: {}".format(labelsPath))
print("[INFO] Object classes file is loading...")
LABELS = open(labelsPath).read().strip().split("\n")
labelsNumber = len(LABELS)
if labelsNumber != 0:
    print("[INFO] Object classes loaded successfully. {} classes loaded.".format(labelsNumber))
else:
    print("[INFO] [ERROR] Empty object classes file.")

np.random.seed(42)
COLORS = np.random.randint(0, 255, size=(len(LABELS), 3), dtype="uint8")

# TODO check for succesfully loaded file using os library
weightsPath = os.path.sep.join([arguments["yolo"], "yolov4-tiny.weights"])
# TODO check for succesfully loaded file using os library
configPath = os.path.sep.join([arguments["yolo"], "yolov4-tiny.cfg"])

print("[INFO] Loading YOLO from disk")
# TODO check for succesfully loaded file
net = cv.dnn.readNetFromDarknet(configPath, weightsPath)
if arguments["gpu"]:
    print("[INFO] Inference on GPU\n")
    net.setPreferableBackend(cv.dnn.DNN_BACKEND_CUDA)
    net.setPreferableTarget(cv.dnn.DNN_TARGET_CUDA)
else:
    print("[INFO] Inference on CPU\n")

ln = net.getLayerNames()
ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

# cap = cv.VideoCapture(0)
camera = nano.Camera()
image = camera.read()
(H, W) = image.shape[:2]

while camera.isReady():
    image = camera.read()
    blob = cv.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layerOutputs = net.forward(ln)
    end = time.time()
    print("[DETECTION] Inference completed in {:.6f} seconds".format(end-start))

    boxes, confidences, classIDs = [], [], []

    for output in layerOutputs:
        for detection in output:
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            if confidence > arguments["confidence"]:
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)

    idxs = cv.dnn.NMSBoxes(boxes, confidences, arguments["confidence"], arguments["threshold"])
    print("[DETECTION] Objects detected: ", classIDs, "\n")
    if len(idxs) > 0:
        font = cv.FONT_HERSHEY_SIMPLEX
        fontSize = .5
        fontThickness = 2
        for i in idxs.flatten():
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])
            textColor = [int(c) for c in COLORS[classIDs[i]]]
            cv.rectangle(image, (x,y), (x+w, y+h), textColor, 2)
            text = "{}: {:.4f}".format(LABELS[classIDs[i]], confidences[i])
            textSize = cv.getTextSize(text, font, fontSize, fontThickness)
            cv.rectangle(image, (x, y-textSize[0][1]-10), (x+textSize[0][0], y), (255,255,255), -1)
            cv.putText(image, text, (x, y - 5), font, fontSize, textColor, fontThickness)
    cv.imshow("Result", image)

    if cv.waitKey(1) == 27:
        break

del camera
cv.destroyAllWindows()