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
    dist = np.array(data.get("dist", [0, 0, 0, 0, 0])).flatten()
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
    print(f"\U0001F680 Running COLMAP {desc}...")
    print("\U0001F6E0️ Command:", " ".join(cmd))
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
        "--ImageReader.camera_model", "OPENCV",
        "--SiftExtraction.use_gpu", "1",
        "--SiftExtraction.max_num_features", "8192"
    ], "feature_extractor")

def run_exhaustive_matcher(colmap_exe, database_path):
    run_cmd(colmap_exe, [
        "exhaustive_matcher",
        "--database_path", database_path
    ], "exhaustive_matcher")

def run_point_triangulator(colmap_exe, database_path, image_path, input_path, output_path):
    run_cmd(colmap_exe, [
        "point_triangulator",
        "--database_path", database_path,
        "--image_path", image_path,
        "--input_path", input_path,
        "--output_path", output_path,
        "--Mapper.tri_ignore_two_view_tracks", "0" # 2-view에서만 match되는 것도 포함
    ], "point_triangulator")

def export_model_to_txt(colmap_exe, input_path):
    run_cmd(colmap_exe, [
        "model_converter",
        "--input_path", input_path,
        "--output_path", input_path,
        "--output_type", "TXT"
    ], "model_converter (BIN → TXT in-place)")

def inspect_database(db_path):
    db = COLMAPDatabase.connect(db_path)
    images = db.execute("SELECT image_id, name FROM images").fetchall()
    print("\U0001F4F8 Registered images:")
    for img_id, name in images:
        print(f"  ID: {img_id}, Name: {name}")
    keypoints_info = db.execute("SELECT COUNT(*), image_id FROM keypoints GROUP BY image_id").fetchall()
    print("\n\U0001F50D Keypoints per image:")
    for count, image_id in keypoints_info:
        print(f"  Image ID {image_id}: {count} keypoints")
    match_pairs = db.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    print(f"\n\U0001F517 Total match pairs: {match_pairs}")
    db.close()

def convert_to_colmap(base_path, colmap_exe):
    extrinsics = load_extrinsics(os.path.join(base_path, "extrinsics.json"))

    database_path = os.path.join(base_path, "database.db")
    images_path = os.path.join(base_path, "images")
    cam_names = sorted([
        f"{d}/{os.listdir(os.path.join(images_path, d))[0]}"
        for d in os.listdir(images_path)
        if d.startswith("cam") and os.path.isdir(os.path.join(images_path, d)) and os.listdir(os.path.join(images_path, d))
    ])
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

    manually_created_sparse_path = os.path.join(base_path, "manually/created/sparse", "0")
    os.makedirs(manually_created_sparse_path, exist_ok=True)
    cameras_path = os.path.join(manually_created_sparse_path, "cameras.txt")
    images_txt_path = os.path.join(manually_created_sparse_path, "images.txt")
    points3D_path = os.path.join(manually_created_sparse_path, "points3D.txt")

    existing_cams = {}
    camera_id = 1
    image_id = 1

    with open(cameras_path, "w") as cam_file, open(images_txt_path, "w") as img_file:
        cam_file.write("# Camera list with one line of data per camera:\n")
        cam_file.write("#   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n")
        img_file.write("# Image list with two lines of data per image:\n")
        img_file.write("#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME\n")
        img_file.write("#   POINTS2D[] as (X, Y, POINT3D_ID)\n")

        for cam_name in cam_names:
            intr_path = os.path.join(images_path, cam_name.split("/")[0], "intrinsics.json")
            w, h, fx, fy, cx, cy, _, dist = load_intrinsics(intr_path)
            if dist.size < 4:
                raise ValueError(f"distortion 계수 4개 이상 필요 (k1, k2, p1, p2). 현재: {dist}")
            k1, k2, p1, p2 = dist[:4]
            params_tuple = (w, h, fx, fy, cx, cy, k1, k2, p1, p2)

            if params_tuple in existing_cams:
                cam_id = existing_cams[params_tuple]
            else:
                cam_id = camera_id
                model = 4  # OPENCV
                db.add_camera(
                    model=model,
                    width=w, height=h,
                    params=np.array([fx, fy, cx, cy, k1, k2, p1, p2]),
                    prior_focal_length=True,
                    camera_id=cam_id
                )
                cam_file.write(f"{cam_id} OPENCV {w} {h} {fx:.12f} {fy:.12f} {cx:.12f} {cy:.12f} {k1:.12f} {k2:.12f} {p1:.12f} {p2:.12f}\n")
                existing_cams[params_tuple] = cam_id
                camera_id += 1
            
            T = np.array(extrinsics[cam_name])
            R_wc = T[:3, :3]
            t_wc = T[:3, 3]
            qvec = R.from_matrix(R_wc).as_quat()
            qw, qx, qy, qz = qvec[3], qvec[0], qvec[1], qvec[2]

            image_name = cam_name
            
            db.execute(
                "INSERT INTO images (image_id, name, camera_id, prior_qw, prior_qx, prior_qy, prior_qz, prior_tx, prior_ty, prior_tz) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (image_id, image_name, cam_id, qw, qx, qy, qz, t_wc[0], t_wc[1], t_wc[2])
            )
            img_file.write(f"{image_id} {qw:.12f} {qx:.12f} {qy:.12f} {qz:.12f} {t_wc[0]:.12f} {t_wc[1]:.12f} {t_wc[2]:.12f} {cam_id} {image_name}\n\n")
            image_id += 1

    with open(points3D_path, "w") as p3d_file:
        p3d_file.write("# 3D point list with one line of data per point:\n")
        p3d_file.write("#   POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as (IMAGE_ID, POINT2D_IDX)\n")
        p3d_file.write("# Number of points: 0, mean track length: 0\n")

    db.commit()
    db.close()

    print("✅ database.db / cameras.txt / images.txt / points3D.txt 구성 완료")
    run_feature_extractor(colmap_exe, database_path, images_path)
    run_exhaustive_matcher(colmap_exe, database_path)
    inspect_database(database_path)

    triangulated_path = os.path.join(base_path, "triangulated", "sparse", "0")
    os.makedirs(triangulated_path, exist_ok=True)
    run_point_triangulator(colmap_exe, database_path, images_path, manually_created_sparse_path, triangulated_path)
    export_model_to_txt(colmap_exe, triangulated_path)

if __name__ == "__main__":
    base_path = r"C:/Users/Kang/Desktop/camera_calibration/multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface"
    colmap_exe = r"C:/Users/Kang/colmap-x64-windows-cuda/COLMAP.bat" # C:/Users/Kang/colmap-x64-windows-cuda/COLMAP.bat or C:/Users/maila/KHS/COLMAP-3.9.1-windows-cuda/COLMAP.bat
    convert_to_colmap(base_path, colmap_exe)
