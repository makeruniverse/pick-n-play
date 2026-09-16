import cv2
import numpy as np
import time

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
aruco_params = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

def detect_aruco(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners, ids, rejected = detector.detectMarkers(gray)
    
    if ids is not None:
        # Draw detected markers
        cv2.aruco.drawDetectedMarkers(image, corners, ids)
        print(f"Detected {len(ids)} marker(s): IDs = {ids.flatten()}")
    return corners, ids, image

def detection_loop():
	cap = cv2.VideoCapture(0)
	time.sleep(2)
  
	while True:
		ret, frame = cap.read()
		frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
		corners, ids, annotated = detect_aruco(frame)
		cv2.imshow('ArUco Detection', cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break