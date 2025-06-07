### ✅ convert_to_COLMAP_fmt.py (중복 intrinsics 통합 반영, sparse/dense 제거, bin 저장만)
import json
import os
import sys
import subprocess
import numpy as np
from scipy.spatial.transform import Rotation as R
import cv2

# COLMAP database.py 경로 등록
sys.path.append(os.path.join(os.path.dirname(__file__), "colmap", "scripts", "python"))
from database import COLMAPDatabase

def load_intrinsics(path):
    with open(path, 'r') as f:
        data = json.load(f)
    mtx = np.array(data["mtx"])
    dist = np.array(data.get("dist", [0, 0, 0, 0, 0]))
    h, w = data.get("resolution", (None, None))
    if h is None or w is None:
        raise ValueError("resolution not provided in intrinsics.json")
    fx, fy = mtx[0, 0], mtx[1, 1]
    cx, cy = mtx[0, 2], mtx[1, 2]
    return w, h, fx, fy, cx, cy, mtx, dist

def load_extrinsics(path):
    with open(path, 'r') as f:
        return json.load(f)

def run_cmd(colmap_exe, args, desc):
    cmd = [colmap_exe] + args
    print(f"🚀 Running COLMAP {desc}...")
    print("🛠️ Command:", " ".join(cmd))
    result = subprocess.run(" ".join(cmd), capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(f"❌ COLMAP {desc} 실패:")
        print(result.stderr)
    else:
        print(f"✅ COLMAP {desc} 성공")
        print(result.stdout)

def run_feature_extractor(colmap_exe, database_path, image_path):
    run_cmd(colmap_exe, [
        "feature_extractor",
        "--database_path", database_path,
        "--image_path", image_path,
        "--ImageReader.single_camera", "0",
        "--ImageReader.camera_model", "PINHOLE",
        "--SiftExtraction.use_gpu", "1"
    ], "feature_extractor")

def run_model_converter(colmap_exe, base_dir):
    sparse_dir = os.path.join(base_dir, "sparse", "0")
    os.makedirs(sparse_dir, exist_ok=True)
    run_cmd(colmap_exe, [
        "model_converter",
        "--input_path", base_dir,
        "--output_path", sparse_dir,
        "--output_type", "BIN"
    ], "model_converter")

def undistort_images(base_dir, image_dir, output_dir):
    cam_dirs = sorted([d for d in os.listdir(base_dir) if d.startswith("cam") and os.path.isdir(os.path.join(base_dir, d))])
    os.makedirs(output_dir, exist_ok=True)
    for cam_name in cam_dirs:
        intr_path = os.path.join(base_dir, cam_name, "intrinsics.json")
        w, h, fx, fy, cx, cy, K, dist = load_intrinsics(intr_path)
        img_path = os.path.join(image_dir, f"{cam_name}.jpg")
        img = cv2.imread(img_path)
        if img is None:
            continue
        undistorted = cv2.undistort(img, K, dist)
        cv2.imwrite(os.path.join(output_dir, f"{cam_name}.jpg"), undistorted)
    print("✅ Undistorted images 저장 완료")

def convert_to_colmap(base_dir, colmap_exe):
    cam_dirs = sorted([d for d in os.listdir(base_dir) if d.startswith("cam") and os.path.isdir(os.path.join(base_dir, d))])
    extrinsics = load_extrinsics(os.path.join(base_dir, "extrinsics.json"))

    database_path = os.path.join(base_dir, "database.db")
    orig_image_dir = os.path.join(base_dir, "images")
    undist_image_dir = os.path.join(base_dir, "images_undistorted")
    os.makedirs(undist_image_dir, exist_ok=True)

    undistort_images(base_dir, orig_image_dir, undist_image_dir)

    if os.path.exists(database_path):
        os.remove(database_path)
    db = COLMAPDatabase.connect(database_path)
    db.create_tables()

    db.execute("ALTER TABLE images ADD COLUMN prior_qw REAL")
    db.execute("ALTER TABLE images ADD COLUMN prior_qx REAL")
    db.execute("ALTER TABLE images ADD COLUMN prior_qy REAL")
    db.execute("ALTER TABLE images ADD COLUMN prior_qz REAL")
    db.execute("ALTER TABLE images ADD COLUMN prior_tx REAL")
    db.execute("ALTER TABLE images ADD COLUMN prior_ty REAL")
    db.execute("ALTER TABLE images ADD COLUMN prior_tz REAL")

    existing_cams = {}
    camera_id = 1
    image_id = 1
    for cam_name in cam_dirs:
        intr_path = os.path.join(base_dir, cam_name, "intrinsics.json")
        w, h, fx, fy, cx, cy, *_ = load_intrinsics(intr_path)
        params_tuple = (w, h, fx, fy, cx, cy)

        if params_tuple in existing_cams:
            cam_id = existing_cams[params_tuple]
        else:
            cam_id = camera_id
            db.add_camera(
                model=1,
                width=w, height=h,
                params=np.array([fx, fy, cx, cy]),
                prior_focal_length=True,
                camera_id=cam_id
            )
            existing_cams[params_tuple] = cam_id
            camera_id += 1

        T = np.array(extrinsics[cam_name])
        R_wc = T[:3, :3]
        t_wc = T[:3, 3]
        qvec = R.from_matrix(R_wc).as_quat()
        qw, qx, qy, qz = qvec[3], qvec[0], qvec[1], qvec[2]

        image_name = f"{cam_name}.jpg"
        db.execute(
            "INSERT INTO images (image_id, name, camera_id, prior_qw, prior_qx, prior_qy, prior_qz, prior_tx, prior_ty, prior_tz) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (image_id, image_name, cam_id, qw, qx, qy, qz, t_wc[0], t_wc[1], t_wc[2])
        )
        image_id += 1

    db.commit()
    db.close()

    print("✅ database.db 구성 완료")
    run_feature_extractor(colmap_exe, database_path, undist_image_dir)
    run_model_converter(colmap_exe, base_dir)

if __name__ == "__main__":
    base_dir = r"C:/Users/maila/KHS/camera_calibration/multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface/images/checkerboard"
    colmap_exe = r"C:/Users/maila/KHS/COLMAP-3.9.1-windows-cuda/COLMAP.bat"
    convert_to_colmap(base_dir, colmap_exe)
