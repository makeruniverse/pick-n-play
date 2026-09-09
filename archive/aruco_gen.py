import cv2
import numpy as np

# Available ArUco dictionaries
# DICT_4X4_50, DICT_6X6_250, DICT_7X7_1000, DICT_ARUCO_ORIGINAL
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

# Generate and save marker with ID 0
for i in range(0, 10):
	marker_id = i
	marker_size = 200  # pixels

	# Create marker image
	marker_img = np.zeros((marker_size, marker_size), dtype=np.uint8)
	cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size, marker_img)
	
	# Add white border for easier detection
	bordered = cv2.copyMakeBorder(marker_img, 20, 20, 20, 20,
                               	cv2.BORDER_CONSTANT, value=255)
	cv2.imwrite(f'./markers/aruco_marker_{marker_id}.png', bordered)
	print(f"Saved aruco_marker_{marker_id}.png")
	print("Print this marker at 10cm x 10cm for pose estimation")