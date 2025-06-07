### ✅ convert_to_COLMAP_fmt.py (통합 + pose 반영 + schema 확장 + matcher + triangulator + sparse model 저장 + 고정된 intrinsics/extrinsics)
import json
import os
import sys
import subprocess
import numpy as np
from scipy.spatial.transform import Rotation as R

# COLMAP database.py 경로 등록
sys.path.append(os.path.join(os.path.dirname(__file__), "colmap", "scripts", "python"))
from database import COLMAPDatabase

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
        return json.load(f)

def run_feature_extractor(colmap_exe, database_path, image_path):
    cmd = [
        colmap_exe, "feature_extractor",
        "--database_path", database_path,
        "--image_path", image_path,
        "--ImageReader.single_camera", "0",
        "--ImageReader.camera_model", "PINHOLE",
        "--SiftExtraction.use_gpu", "1"
    ]
    print("🚀 Running COLMAP feature_extractor...")
    result = subprocess.run(" ".join(cmd), capture_output=True, text=True, shell=True)
    print(result.stdout)

def run_exhaustive_matcher(colmap_exe, database_path):
    cmd = [
        colmap_exe, "exhaustive_matcher",
        "--database_path", database_path,
        "--SiftMatching.use_gpu", "1"
    ]
    print("🚀 Running COLMAP exhaustive_matcher...")
    result = subprocess.run(" ".join(cmd), capture_output=True, text=True, shell=True)
    print(result.stdout)

def run_mapper(colmap_exe, base_dir):
    sparse_dir = os.path.join(base_dir, "sparse")
    os.makedirs(sparse_dir, exist_ok=True)
    cmd = [
        colmap_exe, "mapper",
        "--database_path", os.path.join(base_dir, "database.db"),
        "--image_path", os.path.join(base_dir, "images"),
        "--output_path", sparse_dir,
        "--Mapper.num_threads", "4",
        "--Mapper.ba_refine_focal_length", "0",
        "--Mapper.ba_refine_principal_point", "0",
        "--Mapper.ba_refine_extra_params", "0",
        "--Mapper.ba_refine_positions", "0",
        "--Mapper.ba_refine_rotations", "0"
    ]
    print("🚀 Running COLMAP mapper (sparse reconstruction, fixed intrinsics/extrinsics)...")
    result = subprocess.run(" ".join(cmd), capture_output=True, text=True, shell=True)
    print(result.stdout)

def convert_to_colmap(base_dir, colmap_exe):
    cam_dirs = sorted([d for d in os.listdir(base_dir) if d.startswith("cam") and os.path.isdir(os.path.join(base_dir, d))])
    extrinsics = load_extrinsics(os.path.join(base_dir, "extrinsics.json"))

    database_path = os.path.join(base_dir, "database.db")
    image_path = os.path.join(base_dir, "images")

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

    image_id = 1
    for cam_id, cam_name in enumerate(cam_dirs, start=1):
        intr_path = os.path.join(base_dir, cam_name, "intrinsics.json")
        w, h, fx, fy, cx, cy = load_intrinsics(intr_path)

        db.add_camera(
            model=1,
            width=w, height=h,
            params=np.array([fx, fy, cx, cy]),
            prior_focal_length=True,
            camera_id=cam_id
        )

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
    run_feature_extractor(colmap_exe, database_path, image_path)
    run_exhaustive_matcher(colmap_exe, database_path)
    run_mapper(colmap_exe, base_dir)

if __name__ == "__main__":
    base_dir = r"C:/Users/maila/KHS/camera_calibration/multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface/images/checkerboard"
    colmap_exe = r"C:/Users/maila/KHS/COLMAP-3.9.1-windows-cuda/COLMAP.bat"
    convert_to_colmap(base_dir, colmap_exe)
