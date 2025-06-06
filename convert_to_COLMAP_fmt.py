import json
import os
import numpy as np
from scipy.spatial.transform import Rotation as R

def load_intrinsics(path):
    with open(path, 'r') as f:
        data = json.load(f)
    mtx = np.array(data["mtx"])
    h, w = data.get("resolution", (None, None))
    if h is None or w is None:
        raise ValueError("resolution not provided in intrinsics.json")
    fx, fy = mtx[0, 0], mtx[1, 1]
    cx, cy = mtx[0, 2], mtx[1, 2]
    return w, h, fx, fy, cx, cy

def load_extrinsics(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return data

def convert_to_colmap(base_dir):
    cam_dirs = sorted([
        d for d in os.listdir(base_dir)
        if d.startswith("cam") and os.path.isdir(os.path.join(base_dir, d))
    ])
    extrinsics = load_extrinsics(os.path.join(base_dir, "extrinsics.json"))

    cameras_path = os.path.join(base_dir, "cameras.txt")
    images_path = os.path.join(base_dir, "images.txt")
    points3D_path = os.path.join(base_dir, "points3D.txt")

    with open(cameras_path, "w") as cam_file, open(images_path, "w") as img_file:
        # === cameras.txt 헤더 ===
        cam_file.write("# Camera list with one line of data per camera:\n")
        cam_file.write("#   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n")
        cam_file.write(f"# Number of cameras: {len(cam_dirs)}\n")

        # === images.txt 헤더 ===
        img_file.write("# Image list with two lines of data per image:\n")
        img_file.write("#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME\n")
        img_file.write("#   POINTS2D[] as (X, Y, POINT3D_ID)\n")
        img_file.write(f"# Number of images: {len(cam_dirs)}\n")

        cam_id = 1
        for cam_name in cam_dirs:
            intr_path = os.path.join(base_dir, cam_name, "intrinsics.json")
            w, h, fx, fy, cx, cy = load_intrinsics(intr_path)

            # === cameras.txt ===
            cam_file.write(f"{cam_id} PINHOLE {w} {h} {fx:.12f} {fy:.12f} {cx:.12f} {cy:.12f}\n")

            # === images.txt ===
            T = np.array(extrinsics[cam_name])  # world to cam
            R_wc = T[:3, :3]
            t_wc = T[:3, 3]
            r = R.from_matrix(R_wc)
            qw, qx, qy, qz = r.as_quat()
            qw, qx, qy, qz = qw, qx, qy, qz  # 그대로 사용

            image_id = cam_id
            img_file.write(f"{image_id} {qw:.12f} {qx:.12f} {qy:.12f} {qz:.12f} {t_wc[0]:.12f} {t_wc[1]:.12f} {t_wc[2]:.12f} {cam_id} {cam_name}.jpg\n")
            img_file.write("\n")  # 빈 줄 (POINTS2D 없음)

            cam_id += 1

    # === 빈 points3D.txt 생성 ===
    with open(points3D_path, "w") as p3d_file:
        p3d_file.write("# 3D point list with one line of data per point:\n")
        p3d_file.write("#   POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as (IMAGE_ID, POINT2D_IDX)\n")
        p3d_file.write("# Number of points: 0, mean track length: 0\n")

    print("✅ cameras.txt / images.txt / points3D.txt (빈 구조) 생성 완료")

if __name__ == "__main__":
    base_dir = "multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface/images/checkerboard"
    convert_to_colmap(base_dir)
