import cv2 as cv
import numpy as np
import os
import glob
import json
import logging
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s: %(message)s')
file_handler = logging.FileHandler('./logs/camera_calibration_extrinsics.log', mode='w')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

CHECKERBOARD = (7, 4)
real_world_distance = 30  # mm
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
window_size = (640, 480)

def draw_axes(img, corners, imgpts):
    corner = tuple(corners[0].ravel().astype(int))
    img = cv.line(img, corner, tuple(int(i) for i in imgpts[2].ravel()), (255, 0, 0), 3)
    img = cv.line(img, corner, tuple(int(i) for i in imgpts[1].ravel()), (0, 255, 0), 3)
    img = cv.line(img, corner, tuple(int(i) for i in imgpts[0].ravel()), (0, 0, 255), 3)
    return img

def load_intrinsics(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    return np.array(data["mtx"]), np.array(data["dist"])

def extract_corners(img_path):
    img = cv.imread(img_path)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    ret, corners = cv.findChessboardCorners(gray, CHECKERBOARD, None)
    if not ret:
        logger.warning(f"Checkerboard not found: {img_path}")
        return None, None, img, gray
    corners_refined = cv.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
    return corners_refined, corners, img, gray

def compute_pose(objp, imgpts, mtx, dist):
    ret, rvec, tvec = cv.solvePnP(objp, imgpts, mtx, dist)
    return rvec, tvec

def compose_transform(rvec, tvec):
    R, _ = cv.Rodrigues(rvec)
    T = np.eye(4)
    T[:3,:3] = R
    T[:3, 3] = tvec.ravel()
    return T

def get_object_points():
    objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
    objp *= real_world_distance
    return objp

def plot_camera_poses(cam_poses, axis_length=45):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    colors = ['r', 'g', 'b']

    for cam_name, T in cam_poses.items():
        T = np.array(T)
        origin = T[:3, 3]
        R = T[:3, :3]

        for i in range(3):
            axis_vec = R[:, i] * axis_length
            ax.quiver(*origin, *axis_vec, color=colors[i], linewidth=2)

        ax.text(*origin, cam_name, fontsize=10)

    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_zlabel('Z (mm)')
    ax.set_title('Camera Poses in cam0 Coordinate Frame')
    ax.view_init(elev=20, azim=120)
    ax.grid(True)
    plt.tight_layout()
    plt.show()

def main():
    base_dir = "multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface/images/checkerboard/"
    cam_dirs = sorted([os.path.join(base_dir, d) for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])
    logger.info(f"Cam directories: {cam_dirs}")
    
    intrinsics_path = os.path.join(cam_dirs[0], "intrinsics.json")
    mtx, dist = load_intrinsics(intrinsics_path)
    
    objp = get_object_points()
    axis = np.float32([[real_world_distance, 0, 0],
                       [0, real_world_distance, 0],
                       [0, 0, real_world_distance]]).reshape(-1, 3)

    ref_T = np.eye(4)
    cam_poses = {}
    cam_errors = []
    
    prev_T = ref_T
    prev_corners, _, _, _ = extract_corners(glob.glob(os.path.join(cam_dirs[0], "*.jpg"))[0])
    cam_poses[os.path.basename(cam_dirs[0])] = ref_T.tolist()

    for i in range(len(cam_dirs)):
        cam_name = os.path.basename(cam_dirs[i])
        img_path = glob.glob(os.path.join(cam_dirs[i], "*.jpg"))[0]
        corners2, corners_raw, img, gray = extract_corners(img_path)
        if corners2 is None:
            logger.warning(f"Skipping {cam_name} due to corner extraction failure.")
            continue

        rvec, tvec = compute_pose(objp, corners2, mtx, dist)
        T_rel = compose_transform(rvec, tvec)

        if i == 0:
            abs_T = np.eye(4)
        else:
            abs_T = prev_T @ T_rel

        cam_poses[cam_name] = abs_T.tolist()

        # 시각화
        imgpts, _ = cv.projectPoints(axis, rvec, tvec, mtx, dist)
        img_vis = draw_axes(img, corners2, imgpts)
        img_resized = cv.resize(img_vis, window_size)
        cv.imshow(f'Pose - {cam_name}', img_resized)
        cv.waitKey(500)
        cv.destroyAllWindows()

        # reprojection error 계산
        imgpoints2, _ = cv.projectPoints(objp, rvec, tvec, mtx, dist)
        error = cv.norm(corners2, imgpoints2, cv.NORM_L2) / len(imgpoints2)
        cam_errors.append(error)
        logger.info(f"[{cam_name}] Reprojection error: {error:.4f}")

        prev_T = abs_T
        prev_corners = corners2

    mean_error = np.mean(cam_errors)
    logger.info(f"\nMean reprojection error across all cameras: {mean_error:.4f}")

    # 결과 저장
    extrinsics_path = os.path.join(base_dir, "extrinsics.json")
    with open(extrinsics_path, "w") as f:
        json.dump(cam_poses, f, indent=4)
    logger.info(f"Extrinsics saved to: {extrinsics_path}")

    # 카메라 포즈 시각화 함수 호출
    plot_camera_poses(cam_poses)

if __name__ == "__main__":
    main()
