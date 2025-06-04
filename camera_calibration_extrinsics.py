import cv2 as cv
import numpy as np
import os
import glob
import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s: %(message)s')

file_handler = logging.FileHandler('./logs/monovision.log', mode='w')
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

CHECKERBOARD = (7, 4)
real_world_distance = 30  # mm 단위

window_size = (640, 480)

def draw_axes(img, corners, imgpts): # BGR -> imgpts[2]:R, imgpts[1]:G, imgpts[0]:B
    corner = tuple(corners[0].ravel().astype(int))
    img = cv.line(
        img, corner, tuple(int(i) for i in imgpts[2].ravel()), (255, 0, 0), 5
    )  # R -> x axis
    img = cv.line(
        img, corner, tuple(int(i) for i in imgpts[1].ravel()), (0, 255, 0), 5
    )  # G -> y axis
    img = cv.line(
        img, corner, tuple(int(i) for i in imgpts[0].ravel()), (0, 0, 255), 5
    )  # B -> z axis
    return img

def sort_key(filename):
    # 파일명에서 숫자 부분만 추출
    base_name = os.path.basename(filename)
    prefix, suffix = base_name.split("_")
    # 접두사와 접미사를 숫자로 변환
    prefix_num = int(prefix)
    suffix_num = int(suffix.split(".")[0])  # 확장자 제거
    return prefix_num, suffix_num

# 체커보드 코너 찾기 함수
def find_checkerboard_corners(checkerboard_path):
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001) # EPS 정해진 정확도에 다다르면 알고리즘의 반복 중단 + MAX_ITER 지정한 반복수만큼만 알고리즘 수행 => 둘 중 하나라도 만족하면 알고리즘 stop / 30회, 0.001 정확도로 설정
    objpoints = []  # 3D 점
    imgpoints = []  # 2D 점
    objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2) * real_world_distance
    
    checkerboards = glob.glob(os.path.join(checkerboard_path, "*.png"))
    
    num = 0
    for fname in checkerboards:
        img = cv.imread(fname)
        H, W, _ = img.shape
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY) # 이미지를 gray scale로 변환 

        ret, corners = cv.findChessboardCorners(gray, CHECKERBOARD, None) # 채커보드의 패턴 CHECKERBOARD = (7,4)를 입력
        if ret == True:
            num += 1
            logger.info(f"Find ChessboardCorner --> {os.path.basename(fname)}")
            objpoints.append(objp)
            # 주어진 2D 점에 대한 픽셀 좌표 미세조정
            corners2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria) # 최대 정확도로 코너를 감지하기 위해 11x11크기로 입력을 넣어줌
            imgpoints.append(corners2)
            # 코너 그리기 및 표시
            img = cv.drawChessboardCorners(img, CHECKERBOARD, corners2, ret)

            # Resize the image if needed
            img_resized = cv.resize(img, window_size)
            cv.imshow('chessboard', img_resized)
            cv.waitKey(100)

        cv.destroyAllWindows()
    
    logger.info(f'Total num of chessboards {len(checkerboards)}')
    logger.info(f'Total num of corner found chessboards: {num}')
    return objpoints, imgpoints

def find_checkerboard_axes(checkerboard_path, mtx, dist):
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
    objp[:, :2] = (
        np.mgrid[0 : CHECKERBOARD[0], 0 : CHECKERBOARD[1]].T.reshape(-1, 2)
    * real_world_distance
    )
    extensions = ['jpg', 'png']
    checkerboards = [file for ext in extensions for file in glob.glob(os.path.join(checkerboard_path, f"*.{ext}"))]

    axis = np.float32(
    [
        [real_world_distance, 0, 0],
        [0, real_world_distance, 0],
        [0, 0, real_world_distance],
    ]
    ).reshape(-1, 3)
    for fname in checkerboards:
        img = cv.imread(fname)
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        ret, corners = cv.findChessboardCorners(gray, CHECKERBOARD, None)
        if ret == True:
            # 주어진 2D 점에 대한 픽셀 좌표 미세조정
            corners2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            # Find the rotation and translation vectors.
            retval, rvecs, tvecs, inliers = cv.solvePnPRansac(objp, corners2, mtx, dist)
            # project 3D points to image plane
            imgpts, jac = cv.projectPoints(axis, rvecs, tvecs, mtx, dist)
            img = draw_axes(img, corners2, imgpts)

            # Resize the image if needed
            img_resized = cv.resize(img, window_size)
            cv.imshow('chessboard', img_resized)
            cv.waitKey(100)

        cv.destroyAllWindows()

def calibrate_camera(objpoints, imgpoints, gray):
    ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
    return mtx, dist, rvecs, tvecs

def undistortion(distorted_img_path, undistorted_img_path, mtx, dist, GetOptimalNewCameraMatrix):
    images = sorted(glob.glob(os.path.join(distorted_img_path, "*.png")), key=sort_key)
    logger.info(f'For Undistortion --> GetOptimalNewCameraMatrix: {GetOptimalNewCameraMatrix}')
    for file_path in images:
        img = cv.imread(file_path)
        h, w = img.shape[:2]

        if GetOptimalNewCameraMatrix:
        # Method1: Using GetOptimalNewCameraMatrix for camera intrinsics
            newcameramtx, roi = cv.getOptimalNewCameraMatrix(mtx, dist, (w,h),1,(w,h)) # alpha=1을 줌으로써 왜곡을 펼때 잘라낸 부분을 더 보여줌으로써 전체를 보여줌. alpha=0에 가까우면 펴진 부분만 보게 됨
            dst = cv.undistort(img, mtx, dist, None, newcameramtx)
            x, y, w, h = roi
            dst = dst[y:y+h, x:x+w]
        else:
        # Method2: Using camera intrinsics right away
            dst = cv.undistort(img, mtx, dist, None)

        # Save 
        file_name = os.path.basename(file_path)  # jpg file name
        os.makedirs(undistorted_img_path, exist_ok=True)
        
        if file_name.lower().endswith(".jpg"):
            new_file_name = file_name[:-4] + ".png"
        else:
            new_file_name = file_name
        cv.imwrite(os.path.join(undistorted_img_path, new_file_name), dst)

# 메인 코드 실행
def main(opt_cam, use_virtual_poses):
    dataset_path = "./dataset/d435_180deg@15"
    checkerboard_path = os.path.join(dataset_path, "chessboard_extrinsics")
    distorted_img_path = os.path.join(dataset_path, "0deg_Distorted")
    undistorted_img_path = os.path.join(dataset_path, "0deg_Undistorted")
    os.makedirs(undistorted_img_path, exist_ok=True)

    objpoints, imgpoints = find_checkerboard_corners(checkerboard_path)

    ################# Log calibration error for calculating extrinsics #########################################
    image = cv.imread(glob.glob(os.path.join(checkerboard_path, "*.png"))[0]) # 첫 번째 이미지의 해상도로 이미지 모양 설정
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    mtx, dist, rvecs, tvecs = calibrate_camera(objpoints, imgpoints, gray)
    find_checkerboard_axes(checkerboard_path, mtx, dist)

    mean_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
        error = cv.norm(imgpoints[i], imgpoints2, cv.NORM_L2) / len(imgpoints2)
        mean_error += error
        total_error = mean_error / len(objpoints)
    logger.info("calibration_error: {}".format(total_error))
    
    extrinsics = {
        # Flatten the nested lists using ravel
        "rvecs": [rvec.ravel().tolist() for rvec in rvecs],
        # Flatten the nested lists using ravel
        "tvecs": [tvec.ravel().tolist() for tvec in tvecs],
        "calibration_error": total_error
    }
    logger.info(extrinsics)
    
    with open(os.path.join(dataset_path, "extrinsics.json"), "w") as json_file:
        json.dump(extrinsics, json_file, indent=4)


    ########### load intrinsics (calculated in camera_calibration.py) and undistort images ####################
    with open("intrinsics.json", "r") as file:
        intrinsics = json.load(file)
        mtx = np.array(intrinsics["mtx"])
        dist = np.array(intrinsics["dist"])
    
    undistortion(distorted_img_path, undistorted_img_path, mtx, dist, GetOptimalNewCameraMatrix=opt_cam)
    
    if use_virtual_poses:
        virtual_distorted_img_path = os.path.join(dataset_path, "15deg_up_Distorted")
        virtual_undistorted_img_path = os.path.join(dataset_path, "15deg_up_Unpdistorted")
        os.makedirs(virtual_undistorted_img_path, exist_ok=True)
        undistortion(virtual_distorted_img_path, virtual_undistorted_img_path, mtx, dist, GetOptimalNewCameraMatrix=opt_cam)

if __name__ == "__main__":
    main(opt_cam=True, use_virtual_poses=False)
    