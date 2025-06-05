import cv2 as cv
import numpy as np
import os
import glob
import json
import logging
import matplotlib.pyplot as plt

# ----------------- Logger 설정 -------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s: %(message)s')
file_handler = logging.FileHandler('./logs/camera_calibration_extrinsics.log', mode='w')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# ----------------- 설정 -------------------
CHECKERBOARD = (7, 4)
real_world_distance = 30  # mm
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
window_size = (640, 480)

# ----------------- 함수 정의 -------------------
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
    return corners_refined, corners, img, gray, ret

def compute_pose(objp, imgpts, mtx, dist):
    '''
    The cv::solvePnP() returns the rotation and the translation vectors that transform a 3D point expressed in the object coordinate frame to the camera coordinate frame, using different methods:
    object(checkerboard) frame의 위치가 카메라 프레임에서 어디에 있는가?
    cam0 in board frame -> T_board_to_cam0
    cam1 in board frame -> T_board_to_cam1
    cam2 in board frame -> T_board_to_cam2
    cam3 in board frame -> T_board_to_cam3
    '''
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
    objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2) * real_world_distance
    return objp


def plot_camera_poses(cam_poses, board_pose=None, title="Camera & Checkerboard Poses", axis_length=100):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    cam_colors = ['r', 'g', 'b']  # X, Y, Z

    for cam_name, T in cam_poses.items():
        T = np.array(T)
        origin = T[:3, 3]
        R = T[:3, :3]

        for i in range(3):
            axis_vec = R[:, i] * axis_length
            ax.quiver(*origin, *axis_vec, color=cam_colors[i], linewidth=3, alpha=0.9)
        ax.text(*origin, cam_name, fontsize=10, color='k')

    if board_pose is not None:
        T = np.array(board_pose)
        origin = T[:3, 3]
        R = T[:3, :3]
        board_colors = ['firebrick', 'seagreen', 'royalblue']
        for i in range(3):
            axis_vec = R[:, i] * axis_length
            ax.quiver(*origin, *axis_vec, color=board_colors[i], linewidth=3, alpha=0.9)
        ax.text(*origin, "checkerboard", fontsize=10, color='k')

    axis_range = 600 
    ax.set_xlim(-axis_range, axis_range)
    ax.set_ylim(-axis_range, axis_range)
    ax.set_zlim(-axis_range, axis_range)

    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_zlabel('Z (mm)')
    ax.set_title(title)
    ax.view_init(elev=30, azim=135)
    ax.grid(True)
    ax.set_box_aspect([1, 1, 1])  # 1:1:1 비율 강제
    plt.tight_layout()
    plt.show()


# ----------------- 메인 -------------------
def main():
    base_dir = "multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface/images/checkerboard/"
    cam_dirs = sorted([os.path.join(base_dir, d) for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])
    logger.info(f"Cam directories: {cam_dirs}")

    objp = get_object_points()
    axis = np.float32([[real_world_distance, 0, 0],
                       [0, real_world_distance, 0],
                       [0, 0, real_world_distance]]).reshape(-1, 3)

    cam_poses = {} 
    cam_errors = {}

    for i, cam_path in enumerate(cam_dirs):
        cam_name = os.path.basename(cam_path)
        intrinsics_path = os.path.join(cam_path, "intrinsics.json")
        mtx, dist = load_intrinsics(intrinsics_path)
        img_files = glob.glob(os.path.join(cam_path, "*.jpg"))
        if not img_files:
            logger.warning(f"No image found in {cam_path}")
            continue

        img_path = img_files[0]
        print("img path: ", img_path)
        corners2, _, img, gray, ret= extract_corners(img_path)
        
        # 체커보드 좌표축 2D 이미지에서 시각화
        img = cv.drawChessboardCorners(img, CHECKERBOARD, corners2, ret)

        if corners2 is None:
            logger.warning(f"Skipping {cam_name} due to corner extraction failure.")
            continue

        rvec, tvec = compute_pose(objp, corners2, mtx, dist)
        T_board_to_cami = compose_transform(rvec, tvec) 
        T_cami_to_board = np.linalg.inv(T_board_to_cami)
        
        if i == 0:
            cam_poses[cam_name] = np.eye(4).tolist()
            T_cam0_to_board = T_cami_to_board
            T_board_to_cam0 = T_board_to_cami # cam0 frame에서의 체커보드의 위치
        else:
            T_cam0_to_cami = T_board_to_cami @ T_cam0_to_board
            cam_poses[cam_name] = T_cam0_to_cami.tolist()

        # 재투영 오차 계산
        imgpoints2, _ = cv.projectPoints(objp, rvec, tvec, mtx, dist)
        error = cv.norm(corners2, imgpoints2, cv.NORM_L2) / len(imgpoints2)
        cam_errors[cam_name] = error
        logger.info(f"[{cam_name}] Reprojection error: {error:.4f}")

        # 체커보드 좌표축 2D 이미지에서 시각화
        imgpts, _ = cv.projectPoints(axis, rvec, tvec, mtx, dist)
        img_vis = draw_axes(img, corners2, imgpts)
        img_resized = cv.resize(img_vis, window_size)
        cv.imshow(f'Pose - {cam_name}', img_resized)
        cv.waitKey(1000)
        cv.destroyAllWindows()

    mean_error = np.mean(list(cam_errors.values()))
    logger.info(f"\nMean reprojection error across all cameras: {mean_error:.4f}")

    extrinsics_path = os.path.join(base_dir, "extrinsics.json")
    with open(extrinsics_path, "w") as f:
        json.dump(cam_poses, f, indent=4)
    logger.info(f"Extrinsics saved to: {extrinsics_path}")

    plot_camera_poses(cam_poses, board_pose=T_board_to_cam0.tolist())    
    
if __name__ == "__main__":
    main()

