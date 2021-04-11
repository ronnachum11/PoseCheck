import cv2
import numpy as np
import os

def detectFaceOpenCVDnn(net, frame, framework="caffe", conf_threshold=0.7):
    frameOpencvDnn = frame.copy()
    frameHeight = frameOpencvDnn.shape[0]
    frameWidth = frameOpencvDnn.shape[1]
    if framework == "caffe":
        blob = cv2.dnn.blobFromImage(
            frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], False, False,
        )
    else:
        blob = cv2.dnn.blobFromImage(
            frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False,
        )

    net.setInput(blob)
    detections = net.forward()
    bboxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            x1 = int(detections[0, 0, i, 3] * frameWidth)
            y1 = int(detections[0, 0, i, 4] * frameHeight)
            x2 = int(detections[0, 0, i, 5] * frameWidth)
            y2 = int(detections[0, 0, i, 6] * frameHeight)
            bboxes.append([x1, y1, x2, y2])
            cv2.rectangle(
                frameOpencvDnn,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                int(round(frameHeight / 150)),
                8,
            )
    return frameOpencvDnn, bboxes
    
def getKeyPoints(frame):

    #Import Pose Detection Models
    protoFile = os.path.join("models", "pose", "pose_deploy_linevec.prototxt")
    weightsFile = os.path.join("models", "pose", "pose_iter_440000.caffemodel")
    nPoints = 18
    POSE_PAIRS = [ [1,0],[1,2],[1,5],[2,3],[3,4],[5,6],[6,7],[1,8],[8,9],[9,10],[1,11],[11,12],[12,13],[0,14],[0,15],[14,16],[15,17]]
    net = cv2.dnn.readNetFromCaffe(protoFile, weightsFile)
    net.setPreferableBackend(cv2.dnn.DNN_TARGET_CPU)

    # Import Face Detection Models
    modelFile = os.path.join("models", "facedetect", "res10_300x300_ssd_iter_140000_fp16.caffemodel")
    configFile = os.path.join("models", "facedetect", "deploy.prototxt")
    net2 = cv2.dnn.readNetFromCaffe(configFile, modelFile)

    frameSkeleton = np.copy(frame)
    frameKeyPoints = np.copy(frame)
    facialDetectFrame = np.copy(frame)
    frameWidth = frame.shape[1]
    frameHeight = frame.shape[0]
    threshold = 0.1

    outOpencvDnn, bboxes = detectFaceOpenCVDnn(net2, facialDetectFrame)
    #cv2.imwrite('face-detection.jpg', outOpencvDnn)

    # input image dimensions for the network
    inWidth = 368
    inHeight = 368
    inpBlob = cv2.dnn.blobFromImage(frame, 1.0 / 255, (inWidth, inHeight),
                            (0, 0, 0), swapRB=False, crop=False)

    net.setInput(inpBlob)

    output = net.forward()

    H = output.shape[2]
    W = output.shape[3]

    # Empty list to store the detected keypoints
    points = []

    for i in range(nPoints):
        # confidence map of corresponding body's part.
        probMap = output[0, i, :, :]

        # Find global maxima of the probMap.
        minVal, prob, minLoc, point = cv2.minMaxLoc(probMap)
        
        # Scale the point to fit on the original image
        x = (frameWidth * point[0]) / W
        y = (frameHeight * point[1]) / H

        if prob > threshold : 
            cv2.circle(frameKeyPoints, (int(x), int(y)), 8, (0, 255, 255), thickness=-1, lineType=cv2.FILLED)
            cv2.putText(frameKeyPoints, "{}".format(i), (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, lineType=cv2.LINE_AA)

            # Add the point to the list if the probability is greater than the threshold
            points.append((int(x), int(y)))
        else :
            points.append(None)

    # Draw Skeleton
    for pair in POSE_PAIRS:
        partA = pair[0]
        partB = pair[1]

        if points[partA] and points[partB]:
            cv2.line(frameSkeleton, points[partA], points[partB], (0, 255, 255), 2)
            cv2.circle(frameSkeleton, points[partA], 8, (0, 0, 255), thickness=-1, lineType=cv2.FILLED)

    #cv2.imwrite('Output-Keypoints.jpg', frameKeyPoints)
    #cv2.imwrite('Output-Skeleton.jpg', frameSkeleton)

    for i in range(len(points)):
        if points[i] == None:
            points[i] = (-1, -1)

    keypoints = {
        'Bounding Box' : [bboxes[0][3], bboxes[0][2]],
        'Neck' : [points[1][0], points[1][1]],
        'Nose' : [points[0][0], points[0][1]],
        'Left Eye' : [points[14][0], points[14][1]],
        'Right Eye' : [points[15][0], points[15][1]],
        'Left Ear' :  [points[16][0], points[16][1]],
        'Right Ear' : [points[17][0], points[17][1]],
        'Left Shoulder' : [points[2][0], points[2][1]],
        'Right Shoulder' : [points[5][0], points[5][1]]
    }
    return keypoints

class CheckPosture:
    def __init__(self, scale, key_points={}, baseline_points={}, sensitivity={}):
        self.key_points = key_points
        self.baseline_points = baseline_points
        self.sensitivity = sensitivity
        self.scale = scale
        self.message = ""

    def set_key_points(self, key_points):
        self.key_points = key_points

    def set_basline(self, baseline_points):
        self.baseline_points = baseline_points
        
    def set_basline(self, baseline_points):
        self.baseline_points = baseline_points

    def build_message(self):
        message = ""
        if self.check_proximity()[0]:
            message += "You're too close to the computer screen - try to lean back!!"
        if self.check_slump()[0]:
            message += "Sit up in your chair, you're slumping!"
        if self.check_forward_tilt()[0]:
            message += "Lift up your head!"
        if self.check_head_tilt()[0]:
            if self.check_head_tilt()[1] < 0:
                message += "You're leaning your head to the right! Don't put too much pressure on one side!"
            else:
                message += "You're leaning your head to the left! Don't put too much pressure on one side!"
        if self.check_shoulder_tilt()[0]:
            if self.check_shoulder_tilt()[1] < 0:
                message += "Your left shoulder is higher than your right shoulder! Don't put too much pressure on one side!"
            else:
                message += "Your right shoulder is higher than your left shoulder! Don't put too much pressure on one side!"
        if self.check_shoulder_width()[0]:
            message += "You're curving your shoulders inwards. Try to sit with them further back."
       
        self.message = message
        return message

    def get_message(self):
        return self.message

    def set_scale(self, scale):
        self.scale = scale

    def get_scale(self):
        return self.scale

    def get_distance(self):
        if self.key_points['Bounding Box'][0] != -1 and self.key_points['Bounding Box'][1] != -1:
            v = np.sqrt((self.key_points['Bounding Box'][0] * self.key_points['Bounding Box'][1])/(self.baseline_points['Bounding Box'][0] * self.baseline_points['Bounding Box'][1]))
            return v
        return 1

    def check_proximity(self):
        p1 = self.sensitivity['Proximity'][0]
        p2 = self.sensitivity['Proximity'][1]
        if self.key_points['Bounding Box'][0] != -1 and self.key_points['Bounding Box'][1] != -1:
            v = np.sqrt((self.key_points['Bounding Box'][0] * self.key_points['Bounding Box'][1])/(self.baseline_points['Bounding Box'][0] * self.baseline_points['Bounding Box'][1]))
            if v > p1 or v < p2:
                return [True, v]
        return [False, v]

    def check_slump(self):
        p1 = self.sensitivity['Slump'][0]
        b = self.baseline_points['Nose'][1] - self.baseline_points['Neck'][1]
        if self.key_points['Neck'][1] != -1 and self.key_points['Nose'][1] != -1:
            v = self.key_points['Nose'][1] - self.key_points['Neck'][1]
            if (v - b)/self.get_distance() > p1:
                return [True, (v - b)/self.get_distance()]
            return [False, (v - b)/self.get_distance()]
        return [False, b]

    def check_forward_tilt(self):
        p1 = self.sensitivity['Forward Tilt'][0]
        b = self.baseline_points['Left Eye'][1] - self.baseline_points['Left Ear'][1]
        if self.key_points['Left Eye'][1] != -1  and self.key_points['Left Ear'][1] != -1:
            v = self.key_points['Left Eye'][1] - self.key_points['Left Ear'][1]
            if (v - b)/self.get_distance() > p1:
                return [True, (v - b)/self.get_distance()]
            return [False, (v - b)/self.get_distance()]
        
        b = self.baseline_points['Right Eye'][1] - self.baseline_points['Right Ear'][1]
        if self.key_points['Right Eye'][1] != -1 and self.key_points['Right Ear'][1] != -1:
            v = self.key_points['Right Eye'][1] - self.key_points['Right Ear'][1]
            if (v - b)/self.get_distance() > p1:
                return [True, (v - b)/self.get_distance()]
            return [False, (v - b)/self.get_distance()]
        return [False, b]

    def check_head_tilt(self):
        p1 = self.sensitivity['Head Tilt'][0]
        b = self.baseline_points['Right Ear'][1] - self.baseline_points['Left Ear'][1]
        if self.key_points['Right Ear'][1] != -1 and self.key_points['Left Ear'][1] != -1:
            v = self.key_points['Right Ear'][1] - self.key_points['Left Ear'][1]
            if np.abs((v - b)/self.get_distance()) > p1:
                return [True, (v - b)/self.get_distance()]
            return [False, (v - b)/self.get_distance()]
        return [False, b]

    def check_shoulder_tilt(self):
        b = self.baseline_points['Right Shoulder'][1] - self.baseline_points['Left Shoulder'][1]
        p1 = self.sensitivity['Shoulder Tilt'][0]
        if self.key_points['Right Shoulder'][1] != -1 and self.key_points['Left Shoulder'][1] != -1:
            v = self.key_points['Right Shoulder'][1] - self.key_points['Left Shoulder'][1]
            if np.abs((v - b)/self.get_distance()) > p1:
                return [True, (v - b)/self.get_distance()]
            return [False, (v - b)/self.get_distance()]
        return [False, b]
    
    def check_shoulder_width(self):
        p1 = self.sensitivity['Shoulder Width'][0]
        b = self.baseline_points['Right Shoulder'][0] - self.baseline_points['Left Shoulder'][0]
        if self.key_points['Right Shoulder'][0] != -1 and self.key_points['Left Shoulder'][0] != -1:
            v = self.key_points['Right Shoulder'][0] - self.key_points['Left Shoulder'][0]
            if (np.abs(v) + b)/self.get_distance()  < p1:
                return [True, (np.abs(v) + b)/self.get_distance()]
            return [False, (np.abs(v) + b)/self.get_distance()]
        return [False, b]