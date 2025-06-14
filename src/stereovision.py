import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s: %(message)s')

file_handler = logging.FileHandler('./logs/stereovision.log', mode='w')
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


# Camera parameters to undistort and rectify images
cv_file = cv2.FileStorage()
cv_file.open('stereoMap.xml', cv2.FileStorage_READ)

stereoMapL_x = cv_file.getNode('stereoMapL_x').mat()
stereoMapL_y = cv_file.getNode('stereoMapL_y').mat()
stereoMapR_x = cv_file.getNode('stereoMapR_x').mat()
stereoMapR_y = cv_file.getNode('stereoMapR_y').mat()

# Open both cameras
cam_idxR = 1
cam_idxL = 0

logger.info(f'cam_idxR: {cam_idxR}')
logger.info(f'cam_idxL: {cam_idxL}')

cap_right = cv2.VideoCapture(cam_idxR, cv2.CAP_DSHOW)
cap_left = cv2.VideoCapture(cam_idxL, cv2.CAP_DSHOW)


while(cap_right.isOpened() and cap_left.isOpened()):

    success_right, frame_right = cap_right.read()
    success_left, frame_left = cap_left.read()

    # Undistort and rectify images
    frame_right = cv2.remap(frame_right, stereoMapR_x, stereoMapR_y, cv2.INTER_LANCZOS4, cv2.BORDER_CONSTANT, 0)
    frame_left = cv2.remap(frame_left, stereoMapL_x, stereoMapL_y, cv2.INTER_LANCZOS4, cv2.BORDER_CONSTANT, 0)

    cv2.imshow("frame right", frame_right)
    cv2.imshow("frame left", frame_left)

    
    # Hit "q" to close the window
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# Release and destory all windows before termination
cap_right.release()
cap_left.release()

cv2.destroyAllWindows()