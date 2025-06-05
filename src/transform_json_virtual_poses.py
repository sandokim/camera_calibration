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

file_handler = logging.FileHandler('./logs/transform_json_virtual_poses.log', mode='w')
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

def sort_key(filename):
    # 파일명에서 숫자 부분만 추출
    base_name = os.path.basename(filename)
    prefix, suffix = base_name.split('_')
    # 접두사와 접미사를 숫자로 변환
    prefix_num = int(prefix)
    suffix_num = int(suffix.split('.')[0])  # 확장자 제거
    return prefix_num, suffix_num

def normalize_vector(v):
    """Normalize a vector to have a length of 1."""
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

def plot_axes(ax, matrix, label='', color=['r', 'g', 'b']):
    origin = matrix[:3, 3]
    rotation = matrix[:3, :3]
    x_dir = normalize_vector(rotation[:, 0]) * 100
    y_dir = normalize_vector(rotation[:, 1]) * 100
    z_dir = normalize_vector(rotation[:, 2]) * 100
    ax.quiver(*origin, *x_dir, color=color[0], arrow_length_ratio=0.1, label=f'{label} X-axis')
    ax.quiver(*origin, *y_dir, color=color[1], arrow_length_ratio=0.1, label=f'{label} Y-axis')
    ax.quiver(*origin, *z_dir, color=color[2], arrow_length_ratio=0.1, label=f'{label} Z-axis')

def load_json_data(file_path):
    with open(file_path, "r") as file:
        return json.load(file)
    
def compute_w2g_transforms(wcs, angle_increment, num_transforms):
    w2g_transforms = []

    for i in range(num_transforms):
        angle_radian = np.radians(angle_increment * i)
        R, _ = cv.Rodrigues(np.array([0, angle_radian, 0]))  # Y-axis rotation
        transformation_matrix = np.eye(4)
        transformation_matrix[:3, :3] = R

        w2g_transform = wcs @ transformation_matrix
        w2g_transforms.append(w2g_transform)

    return w2g_transforms

def compute_g2f_transforms(w2g_transforms, trans_x, trans_y, trans_z):
    translation_vector = np.array([trans_x, trans_y, trans_z])
    g2f = np.eye(4)
    g2f[:3, 3] += translation_vector

    g2f_transforms = []
    for _ in range(len(w2g_transforms)):
        g2f_transforms.append(g2f)

    return g2f_transforms

def compute_c2f_transforms(c2w, w2g_transforms, g2f_transforms):
    c2f_transforms = []
    for i, (w2g, g2f) in enumerate(zip(w2g_transforms, g2f_transforms)):
        c2f = c2w @ w2g @ g2f
        c2f_transforms.append(c2f)
    return c2f_transforms

def compute_virtual_transforms(f2c_transforms, axis, deg):
    # Mid camera 15 deg rotation
    rotation_matrix = R.from_euler(axis, deg, degrees=True).as_matrix()
    mid_idx = len(f2c_transforms) // 2 - 1
    mid_cam = np.copy(f2c_transforms[mid_idx])
    mid_cam_pos = rotation_matrix @ mid_cam[:3, 3]
    mid_cam_dir = rotation_matrix @ mid_cam[:3, :3]
    mid_cam_15up = np.eye(4)
    mid_cam_15up[:3, 3] = mid_cam_pos
    mid_cam_15up[:3, :3] = mid_cam_dir
    
    virtual_transforms = []
    for angle in range(-90, 90, 5):
        # Y축을 중심으로 회전시키는 행렬을 생성합니다.
        
        rotation_matrix = R.from_euler('y', -angle, degrees=True).as_matrix()

        # 포즈의 위치를 회전시킨 후 새 위치를 계산합니다.
        rotated_position = rotation_matrix @ mid_cam_15up[:3, 3]

        # 포즈의 방향(회전 부분)도 회전시킵니다.
        rotated_axis = rotation_matrix @ mid_cam_15up[:3, :3]

        # 새로운 포즈를 생성합니다.
        virtual_transform = np.copy(mid_cam_15up)
        virtual_transform[:3, 3] = rotated_position
        virtual_transform[:3, :3] = rotated_axis

        # 업데이트된 포즈를 리스트에 추가합니다.
        virtual_transforms.append(virtual_transform)
    
    return virtual_transforms
        
def save_dataset(images, transforms, dataset_dir, intrinsics):
    """
    Saves images and transformation matrices into training and testing datasets.
    """
    # Create directories if they don't exist
    test_dir = os.path.join(dataset_dir, 'test')
    train_dir = os.path.join(dataset_dir, 'train')
    os.makedirs(test_dir, exist_ok=True)
    os.makedirs(train_dir, exist_ok=True)

    data_test = {"camera_angle_x": intrinsics["camera_angle_x"], "frames": []}
    data_train = {"camera_angle_x": intrinsics["camera_angle_x"], "frames": []}
    
    data_all = {"camera_angle_x": intrinsics["camera_angle_x"], "frames": []}

    # Divide images into train and test datasets
    for i, (file_path, transform) in enumerate(zip(images, transforms)):
        base_name = os.path.basename(file_path)
        dataset_type = 'test' if i % 8 == 0 else 'train'
        dataset_path = test_dir if dataset_type == 'test' else train_dir
        frame_data = {
            "file_path": f"{dataset_type}/{base_name.split('.')[0]}",
            "transform_matrix": transform.tolist()
        }

        # Split json information into train / test
        if dataset_type == 'test':
            data_test["frames"].append(frame_data)
        else:
            data_train["frames"].append(frame_data)
            
            
        # json information
        frame_data_all = {
            "file_path": f"{base_name.split('.')[0]}",
            "transform_matrix": transform.tolist()
        }
        data_all["frames"].append(frame_data_all)
        
        # Copy to train / test folder
        dataset_path = test_dir if dataset_type == 'test' else train_dir
        shutil.copy(file_path, os.path.join(dataset_path, base_name))

    # Save the test and train data to JSON files
    with open(os.path.join(dataset_dir, 'transforms_test.json'), 'w') as outfile:
        json.dump(data_test, outfile, indent=4)
    with open(os.path.join(dataset_dir, 'transforms_train.json'), 'w') as outfile:
        json.dump(data_train, outfile, indent=4)
    
    # Save all data to JSON files
    with open(os.path.join(dataset_dir, 'transforms.json'), 'w') as outfile:
        json.dump(data_all, outfile, indent=4)   
        


def main(use_virtual_poses):
    dataset_dir = "./dataset/d435_180deg@15"
    c2w = np.array(load_json_data(os.path.join(dataset_dir, "c2w.json")))
    w2c = np.array(load_json_data(os.path.join(dataset_dir, "w2c.json")))
    wcs = np.array(load_json_data(os.path.join(dataset_dir, "wcs.json")))
    intrinsics = load_json_data("intrinsics.json")

    real_dir = '0deg_Undistorted'
    virtual_dir = '15deg_up_Undistorted'
    
    logger.info(f'dataset_dir: {dataset_dir}')
    logger.info(f'use_virtual_poses: {use_virtual_poses}')
    
    images = sorted(glob.glob(os.path.join(dataset_dir, real_dir, '*.png')), key=sort_key)

    w2g_transforms = compute_w2g_transforms(wcs=wcs, angle_increment=-15, num_transforms=len(images))
    g2f_transforms = compute_g2f_transforms(w2g_transforms, trans_x=0, trans_y=-0, trans_z=0)
    c2f_transforms = compute_c2f_transforms(c2w, w2g_transforms, g2f_transforms)

    f2c_transforms = [np.linalg.inv(c2f_transforms[i]) for i in range(len(c2f_transforms))]
    
    if use_virtual_poses:
        virtual_images = sorted(glob.glob(os.path.join(dataset_dir, virtual_dir, '*.png')), key=sort_key)
        images.extend(virtual_images)
        virtual_transforms = compute_virtual_transforms(f2c_transforms, axis='z', deg=-15)
        f2c_transforms.extend(virtual_transforms)
        
    # Set Axes direction to NeRF dataset style: left, down, back --> right, up, back
    f2c_transforms = [np.concatenate([f2c_transforms[i][:, 0:1], -f2c_transforms[i][:, 1:2], -f2c_transforms[i][:, 2:3], f2c_transforms[i][:, 3:4]],-1) for i in range(len(f2c_transforms))]
    
    # c2w, g2w_transforms plot
    fig1, ax1 = setup_plot("WCS 기준: W2C, W2G poses")
    for i, w2g in enumerate(w2g_transforms):
        plot_axes(ax1, w2g, label=f'Gripper {i}', color=['coral', 'lightgreen', 'lightblue'])
    plot_axes(ax1, wcs, label='WCS', color=['crimson', 'limegreen', 'dodgerblue'])
    plot_axes(ax1, w2c, label='W2C', color=['r', 'g', 'b'])
    
    fig2, ax2 = setup_plot("WCS(=FCS) 기준: W2C(=F2C) poses")
    # f2c_transforms = f2c_transforms[0:25]
    for i, f2c in enumerate(f2c_transforms):
        plot_axes(ax2, f2c, label=f'F2C {i}', color=['firebrick', 'chartreuse', 'steelblue'])
    plot_axes(ax2, wcs, label='WCS', color=['crimson', 'limegreen', 'dodgerblue'])
    plt.show()

    '''
    - 기준좌표계의 값을 각 얼굴 좌표계별 좌표값으로 변환해주는 transform으로 정의
    - NeRF에서는 'transform_matrix'를 c2w로 명명하여 불러씀
    - 이때 기준좌표계의 값은 추후 NeRF, 3dgs에서 따로 wcs기준 좌표계기준 좌표값이 들어감
    - NeRF는 grid를 정의, 3dgs는 point clouds의 좌표값
    '''
    transforms = []
    for f2c in f2c_transforms:
        f2c[0:3, 3] /= 1000 # mm --> m 단위 변환
        transforms.append(f2c)

    for i in range(len(transforms)):
        logger.info(f'\n transforms_{i}th: \n {transforms[i]}')

    save_dataset(images, transforms, dataset_dir, intrinsics)
if __name__ == "__main__":
    main(use_virtual_poses=False)
