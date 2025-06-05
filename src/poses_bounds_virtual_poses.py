import cv2 as cv
import numpy as np
import json
import glob
import os
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt
import shutil
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s: %(message)s')

file_handler = logging.FileHandler('./logs/poses_bounds_virtual_poses.log', mode='w')
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

'''
Copy from transform_json_virtual_poses.py
'''
        
def save_poses_bounds(images, transforms, near, far, calibration_data):
    poses_bounds_list = []
    poses_matrices_3x5 = []
    for i, file_path in enumerate(images):
        img = cv.imread(file_path)
        H, W, _ = img.shape

        # f_x 사용 / llff dataset에선 f_x, f_y가 같다는 가정을 함
        hwf = [H, W, np.array(calibration_data['cameraIntrinsics'])[0, 0]]

        # Concatenate to get the 3x5 pose matrix
        pose_matrix_3x5 = np.hstack([transforms[i][:3, :4], np.array(hwf).reshape(-1, 1)])

        # Flatten and concatenate the near and far depths
        pose_flat = pose_matrix_3x5.flatten()
        bounds = np.array([near, far])  # near and far values
        pose_bound = np.hstack([pose_flat, bounds])
        
        poses_matrices_3x5.append(pose_matrix_3x5)
        poses_bounds_list.append(pose_bound)
    
    poses_bounds = np.vstack(poses_bounds_list)
    
    logger.info(f'\n3x5 pose 0:\n{np.array2string(poses_matrices_3x5[0], separator=", ", precision=2, floatmode="fixed")}')
    logger.info(f'\nFlatten pose 0:\n{np.array2string(poses_bounds[0], separator=",", precision=2, max_line_width=np.inf)}')
    logger.info(f'poses_bounds shape: {poses_bounds.shape}')
    np.save('poses_bounds.npy', poses_bounds)
    

def main():
    c2w = np.array(load_json_data("c2w.json"))
    calibration_data = load_json_data("calibration.json")
    near = 0.5
    far = 1.5
    
    save_poses_bounds(images, f2c_transforms, near, far, calibration_data)

if __name__ == "__main__":
    
'''
Copy from transform_json_virtual_poses.py
'''
           
