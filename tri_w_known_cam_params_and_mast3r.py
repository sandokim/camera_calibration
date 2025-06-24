import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
import cv2
import torch
from PIL import Image
from collections import defaultdict

# MASt3R 및 DUST3R 관련 모듈 임포트
sys.path.insert(0, os.path.abspath("submodules/mast3r"))
from submodules.mast3r.mast3r.model import AsymmetricMASt3R
from submodules.mast3r.mast3r.fast_nn import fast_reciprocal_NNs
from submodules.mast3r.dust3r.dust3r.inference import inference
from submodules.mast3r.dust3r.dust3r.utils.image import load_images as load_images_for_mast3r

# 3D 시각화를 위한 라이브러리
from mpl_toolkits.mplot3d import Axes3D

# ----- 설정 -----
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model_name = "naver/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric"
mast3r_model = AsymmetricMASt3R.from_pretrained(model_name).to(device)
print(f"MASt3R model loaded on {device}")

BASE_DIR = "multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface"
IMAGE_DIR = os.path.join(BASE_DIR, "images")
CAMERAS = ['cam0', 'cam1', 'cam2', 'cam3']
INTRINSICS_PATHS = [os.path.join(IMAGE_DIR, cam, "intrinsics.json") for cam in CAMERAS]
EXTRINSICS_PATH = os.path.join(BASE_DIR, "extrinsics.json")

# 삼각측량을 위한 최소 뷰 개수 설정
MIN_VIEWS_FOR_TRIANGULATION = 2

# ----- 헬퍼 및 데이터 로드 함수 (이전과 동일) -----
def get_camera_center(P):
    U, D, Vt = np.linalg.svd(P)
    C = Vt[-1, :4]
    return C / C[3]

def visualize_point_cloud(points_3d, colors, camera_matrices):
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(points_3d[:, 0], points_3d[:, 1], points_3d[:, 2], c=colors / 255.0, s=1, label="Reconstructed Points")

    for i, P in enumerate(camera_matrices):
        center = get_camera_center(P)[:3]
        M = P[:, :3]
        principal_axis = np.sign(np.linalg.det(M)) * M[2, :]
        principal_axis /= np.linalg.norm(principal_axis)
        
        ax.scatter(center[0], center[1], center[2], c='magenta', marker='^', s=150, label=f'Cam {i}')
        ax.quiver(center[0], center[1], center[2], principal_axis[0], principal_axis[1], principal_axis[2], 
                  length=np.mean(np.abs(points_3d)) * 0.3, color='magenta', arrow_length_ratio=0.3)

    ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
    ax.set_title(f"MASt3R + Triangulation (Tracks with >= {MIN_VIEWS_FOR_TRIANGULATION} views)")
    
    ref_camera_center = get_camera_center(camera_matrices[0])[:3]
    mid_x, mid_y, mid_z = ref_camera_center[0], ref_camera_center[1], ref_camera_center[2]
    fixed_half_range = 300.0
    
    ax.set_xlim(mid_x - fixed_half_range, mid_x + fixed_half_range)
    ax.set_ylim(mid_y - fixed_half_range, mid_y + fixed_half_range)
    ax.set_zlim(mid_z - fixed_half_range, mid_z + fixed_half_range)
    
    handles, labels = ax.get_legend_handles_labels()
    unique_labels = dict(zip(labels, handles))
    ax.legend(unique_labels.values(), unique_labels.keys())
    
    plt.show()

def load_images_cv() -> (List[np.ndarray], List[str]):
    image_paths = []
    for cam in CAMERAS:
        cam_dir = os.path.join(IMAGE_DIR, cam)
        files = sorted([f for f in os.listdir(cam_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        if files: image_paths.append(os.path.join(cam_dir, files[0]))
        else: raise FileNotFoundError(f"No images found in {cam_dir}")
    images = [cv2.imread(p) for p in image_paths]
    if any(img is None for img in images): raise ValueError("하나 이상의 이미지를 로드하는 데 실패했습니다.")
    return images, image_paths

def load_intrinsics() -> List[np.ndarray]:
    return [np.array(json.load(open(path))["mtx"]) for path in INTRINSICS_PATHS]

def load_extrinsics(image_rel_paths: List[str]) -> List[np.ndarray]:
    with open(EXTRINSICS_PATH, 'r') as f: data = json.load(f)
    Ps = []
    for rel_path in image_rel_paths:
        rel_key = os.path.join(*rel_path.split(os.sep)[-2:]).replace('\\', '/')
        if rel_key not in data: raise ValueError(f"{rel_key} not found in extrinsics.json")
        Ps.append(np.array(data[rel_key])[:3, :])
    return Ps


# ----- MASt3R을 이용한 특징 추출 및 트랙 생성 (개선된 로직) -----
def extract_mast3r_tracks(image_paths: List[str], model: AsymmetricMASt3R, device: torch.device) -> List[List[Tuple[float, float]]]:
    n_views = len(image_paths)
    ref_view_idx = 0  # 0번 카메라를 기준으로 설정
    all_matches = {}

    # 1. 기준 뷰와 다른 모든 뷰 간의 매칭 수행
    for j in range(ref_view_idx + 1, n_views):
        i = ref_view_idx
        print(f"  - Matching reference view {i} and view {j}")
        images_pair = load_images_for_mast3r([image_paths[i], image_paths[j]], size=512)
        
        with torch.no_grad():
            output = inference([tuple(images_pair)], model, device, batch_size=1, verbose=False)
        
        desc1, desc2 = output['pred1']['desc'].squeeze(0).detach(), output['pred2']['desc'].squeeze(0).detach()
        matches_im0, matches_im1 = fast_reciprocal_NNs(desc1, desc2)

        pts_i, pts_j = matches_im0, matches_im1

        if len(pts_i) < 8: continue
        F, mask = cv2.findFundamentalMat(pts_i, pts_j, cv2.FM_RANSAC, 0.5, 0.999)
        if mask is None: continue

        inlier_mask = mask.ravel() == 1
        all_matches[(i, j)] = (pts_i[inlier_mask], pts_j[inlier_mask])
        print(f"    - Found {len(all_matches[(i,j)][0])} inlier matches for pair ({i}, {j})")

    # 2. 기준 뷰 기반으로 트랙 생성
    print("\n  - Building tracks based on reference view...")
    
    # 기준 뷰의 점(튜플)을 키로, 트랙 리스트의 인덱스를 값으로 가짐
    ref_point_to_track_idx = {}
    tracks = []
    
    for j in range(ref_view_idx + 1, n_views):
        if (ref_view_idx, j) not in all_matches:
            continue
            
        pts_ref, pts_j = all_matches[(ref_view_idx, j)]
        
        for p_ref, p_j in zip(pts_ref, pts_j):
            p_ref_tuple = tuple(p_ref)
            
            if p_ref_tuple not in ref_point_to_track_idx:
                # 새로운 점이면 새로운 트랙 생성
                new_track_id = len(tracks)
                new_track = [None] * n_views
                new_track[ref_view_idx] = p_ref
                new_track[j] = p_j
                tracks.append(new_track)
                ref_point_to_track_idx[p_ref_tuple] = new_track_id
            else:
                # 기존에 있던 점이면 해당 트랙에 추가
                track_id = ref_point_to_track_idx[p_ref_tuple]
                tracks[track_id][j] = p_j
                
    return tracks

# ----- 전체 파이프라인 -----
def main():
    print("[1] 이미지 로드 중...")
    images_cv, image_paths = load_images_cv()
    print(f"  - {len(images_cv)}개 이미지 로드 완료.")

    print("[2] 카메라 파라미터 로드 중...")
    Ks = load_intrinsics()
    Ps_raw = load_extrinsics(image_paths)
    Ps = [K @ P_raw for K, P_raw in zip(Ks, Ps_raw)]
    print("  - Intrinsics 및 Extrinsics 로드 완료.")

    print("[3] MASt3R 특징 추출 및 트랙 생성 중...")
    tracks = extract_mast3r_tracks(image_paths, mast3r_model, device)
    
    # 최소 MIN_VIEWS_FOR_TRIANGULATION 개 이상의 뷰에서 보이는 트랙만 필터링
    valid_tracks = [track for track in tracks if sum(p is not None for p in track) >= MIN_VIEWS_FOR_TRIANGULATION]
    num_valid_tracks = len(valid_tracks)
    print(f"  - {num_valid_tracks}개의 유효한 트랙 생성 완료 (관측 뷰 >= {MIN_VIEWS_FOR_TRIANGULATION}).")

    if num_valid_tracks == 0:
        print("삼각측량을 수행할 트랙이 없습니다.")
        return

    print("[4] 3D 포인트 삼각측량 중...")
    points_3d = []
    colors = []

    for track in valid_tracks:
        views = [(i, pt) for i, pt in enumerate(track) if pt is not None]
        
        # 이 필터링은 위에서 이미 했지만, 안전을 위해 유지
        if len(views) < 2: continue
            
        pts2d = [np.array(pt, dtype=np.float64).reshape(2, 1) for _, pt in views]
        Ps_track = [Ps[i] for i, _ in views]
        
        point3d_mat = cv2.sfm.triangulatePoints(pts2d, Ps_track)
        points_3d.append(point3d_mat.flatten())

        first_valid_view_idx, pt0 = views[0]
        x, y = map(int, pt0)
        colors.append(images_cv[first_valid_view_idx][y, x][::-1])

    if not points_3d:
        print("  - 유효한 3D 포인트가 생성되지 않았습니다.")
        return

    points_3d = np.array(points_3d)
    colors = np.array(colors)
    print(f"  - {len(points_3d)}개의 3D 포인트 복원 완료.")

    print("[5] 3D 포인트 클라우드 시각화 중...")
    visualize_point_cloud(points_3d, colors, Ps)

if __name__ == "__main__":
    main()