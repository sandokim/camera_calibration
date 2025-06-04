import os
import cv2
import numpy as np
import json
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s: %(message)s')

file_handler = logging.FileHandler('./logs/hand_eye_calibration.log', mode='w')
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

def setup_plot(title):
    fig = plt.figure()
    fig.canvas.manager.set_window_title(title)
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_xlim([-700, 700])
    ax.set_ylim([-700, 700])
    ax.set_zlim([-700, 700])
    return fig, ax

def load_extrinsics(file_path):
    with open(file_path, "r") as file:
        extrinsics = json.load(file)
        rvecs = [np.array(vec) for vec in extrinsics["rvecs"]]
        tvecs = [np.array(vec) for vec in extrinsics["tvecs"]]
    return rvecs, tvecs

def compute_cam_to_target_transforms(rvecs, tvecs):
    c2t_transforms = []
    for rvec, tvec in zip(rvecs, tvecs):
        R, _ = cv2.Rodrigues(rvec)
        c2t = np.eye(4)
        c2t[:3, :3] = R
        c2t[:3, 3] = tvec
        c2t_transforms.append(c2t)
    return c2t_transforms

def compute_world_to_gripper_transforms(wcs, rvecs, angle_increment):
    w2g_transforms = []
    translation_vector = np.array([0, 0, 0, 1]) # [trans_x, trans_y, trans_z, 1]
    wcs[:, 3] = translation_vector

    for i in range(len(rvecs)):
        # Convert angle increment to radians and compute rotation matrix
        angle = np.radians(angle_increment * i)
        R, _ = cv2.Rodrigues(np.array([0, angle, 0]))  # Rotation around Y-axis

        w2g = np.eye(4)
        w2g[:3, :3] = R
        w2g[:3, 3] = np.array([0, 0, 0])  # Assuming no translation

        # Apply transformation to the world coordinate system
        w2g_transforms.append(wcs @ w2g)

    return w2g_transforms

def perform_hand_eye_calibration(w2g_R, w2g_t, t2c_R, t2c_t):
    w2c_R, w2c_t = cv2.calibrateHandEye(w2g_R, w2g_t, t2c_R, t2c_t, method=cv2.CALIB_HAND_EYE_TSAI)
    w2c = np.eye(4)
    w2c[:3, :3] = w2c_R
    w2c[:3, 3] = w2c_t[:, 0]
    return w2c

def plot_axes(ax, matrix, label='', color=['r', 'g', 'b']):
    origin = matrix[:3, 3]
    rotation = matrix[:3, :3]
    x_dir = normalize_vector(rotation[:, 0]) * 100
    y_dir = normalize_vector(rotation[:, 1]) * 100
    z_dir = normalize_vector(rotation[:, 2]) * 100
    ax.quiver(*origin, *x_dir, color=color[0], arrow_length_ratio=0.1, label=f'{label} X-axis')
    ax.quiver(*origin, *y_dir, color=color[1], arrow_length_ratio=0.1, label=f'{label} Y-axis')
    ax.quiver(*origin, *z_dir, color=color[2], arrow_length_ratio=0.1, label=f'{label} Z-axis')
    # ax.legend()

def normalize_vector(v):
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

def save_transform_to_json(transform, file_path):
    serialized_transform = transform.tolist()
    with open(file_path, "w") as file:
        json.dump(serialized_transform, file)
    print(f'{file_path} saved!')

def main():
    dataset_path = "./dataset/d435_180deg@15"
    rvecs, tvecs = load_extrinsics(os.path.join(dataset_path,"extrinsics.json"))

    # Compute target to cam transforms
    c2t_transforms = compute_cam_to_target_transforms(rvecs, tvecs)
    # Compute world to gripper transforms
    wcs = np.eye(4)  
    w2g_transforms = compute_world_to_gripper_transforms(wcs, rvecs, 5)  

    # Perform Hand-Eye Calibration / w2g & t2c
    w2c = perform_hand_eye_calibration([T[:3, :3] for T in w2g_transforms], [T[:3, 3] for T in w2g_transforms], [T[:3, :3] for T in c2t_transforms], [T[:3, 3] for T in c2t_transforms]) # World 기준 Camera pose
    c2w = np.linalg.inv(w2c)
    # plot turnable table, camera, world relationships
    fig1, ax1 = setup_plot("WCS 기준: W2C, W2G poses")
    for i, w2g in enumerate(w2g_transforms):
        plot_axes(ax1, w2g, label=f'Gripper {i}', color=['coral', 'lightgreen', 'lightblue'])
    # plot_axes(ax1, w2c, label='W2C', color=['r', 'g', 'b'])
    plot_axes(ax1, w2c, label='W2C', color=['r', 'g', 'b']) # 여기서 말하는 c2w가 
    plot_axes(ax1, w2g_transforms[0], label='WCS', color=['crimson', 'limegreen', 'dodgerblue']) # wcs = w2g_transforms[0]

    # Camera & Target relationships
    fig2, ax2= setup_plot("CCS 기준: Target(chessboard) poses")
    # Computer target to world transforms
    for i, c2t in enumerate(c2t_transforms):
        plot_axes(ax2, c2t, label=f'Camera {i}', color=['coral', 'lightgreen', 'lightblue']) # Camera 기준 Target의 위치    
    plot_axes(ax2, wcs, label='Camera pose', color=['r', 'g', 'b']) # Given c2t transforms, Camera Coordinate System located at (0,0,0)
    
    plt.show()
    
    save_transform_to_json(c2w, os.path.join(dataset_path, "c2w.json"))
    save_transform_to_json(w2c, os.path.join(dataset_path, "w2c.json"))
    save_transform_to_json(wcs, os.path.join(dataset_path, "wcs.json"))
    
    # c2w, t2w, g2w
    logger.info(f'\n c2w: \n {c2w}')
    logger.info(f'\n w2c: \n {w2c}')
    logger.info(f'\n wcs: \n {wcs}')
    
    
if __name__ == "__main__":
    main()
