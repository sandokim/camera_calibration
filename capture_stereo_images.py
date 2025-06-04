import cv2
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s: %(message)s')

file_handler = logging.FileHandler('./logs/capture_stereo_images.log', mode='w')
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

cam_idxR = 1
cam_idxL = 0

logger.info(f'cam_idxR: {cam_idxR}')
logger.info(f'cam_idxL: {cam_idxL}')

capR = cv2.VideoCapture(cam_idxR)
capL = cv2.VideoCapture(cam_idxL)

num = 0

while capR.isOpened():

    successR, imgR = capR.read()
    successL, imgL = capL.read()

    k = cv2.waitKey(5)

    if k == 27:
        break
    elif k == ord('s'):
        cv2.imwrite('images/stereoRight/imageR' + str(num) + '.png', imgR)
        cv2.imwrite('images/stereoLeft/imageL' + str(num) + '.png', imgL)
        logger.info(f"image {num} saved!")
        num += 1

    cv2.imshow('Img R', imgR)
    cv2.imshow('Img L', imgL)

capR.release()
capL.release()

cv2.destroyAllWindows()

