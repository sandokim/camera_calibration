import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple
import cv2
import torch
from matplotlib import pyplot as pl

# MASt3R 및 DUST3R 관련 모듈 임포트
# Make sure the paths to the submodules are correct.
sys.path.insert(0, os.path.abspath("submodules/mast3r"))
from submodules.mast3r.mast3r.model import AsymmetricMASt3R
from submodules.mast3r.mast3r.fast_nn import fast_reciprocal_NNs
from submodules.mast3r.dust3r.dust3r.inference import inference
from submodules.mast3r.dust3r.dust3r.utils.image import load_images as load_images_for_mast3r

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

# 2D-2D 매칭결과 시각화할 개수
n_viz = 20
# 삼각측량을 위한 최소 뷰 개수 설정 (현재 로직에서는 직접 사용되지 않음)
MIN_VIEWS_FOR_TRIANGULATION = 2

# ----- 헬퍼 및 데이터 로드 함수 -----
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
    ax.set_title(f"MASt3R + 2-View Triangulation")
    
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

# ----- MASt3R을 이용한 특징 추출 및 2-view 삼각측량 -----
def extract_and_triangulate_pairs(image_paths: List[str], images_cv: List[np.ndarray], Ps: List[np.ndarray], model: AsymmetricMASt3R, device: torch.device) -> Tuple[np.ndarray, np.ndarray]:
    n_views = len(image_paths)
    ref_view_idx = 0
    all_points_3d = []
    all_colors = []

    for j in range(ref_view_idx + 1, n_views):
        i = ref_view_idx
        print(f"\n- Processing Pair: View {i} and View {j}")
        
        print(f"  - Matching reference view {i} and view {j}")
        images_pair = load_images_for_mast3r([image_paths[i], image_paths[j]], size=512)
        
        with torch.no_grad():
            output = inference([tuple(images_pair)], model, device, batch_size=1, verbose=False)
        
        view1, pred1 = output['view1'], output['pred1']
        view2, pred2 = output['view2'], output['pred2']

        desc1, desc2 = pred1['desc'].squeeze(0).detach(), pred2['desc'].squeeze(0).detach()

        matches_im0, matches_im1 = fast_reciprocal_NNs(desc1, desc2, subsample_or_initxy1=8,
                                                       device=device, dist='dot', block_size=2**13)

        H0, W0 = view1['true_shape'][0]
        valid_matches_im0 = (matches_im0[:, 0] >= 3) & (matches_im0[:, 0] < int(W0) - 3) & \
                            (matches_im0[:, 1] >= 3) & (matches_im0[:, 1] < int(H0) - 3)

        H1, W1 = view2['true_shape'][0]
        valid_matches_im1 = (matches_im1[:, 0] >= 3) & (matches_im1[:, 0] < int(W1) - 3) & \
                            (matches_im1[:, 1] >= 3) & (matches_im1[:, 1] < int(H1) - 3)

        valid_matches = valid_matches_im0 & valid_matches_im1
        matches_im0, matches_im1 = matches_im0[valid_matches], matches_im1[valid_matches]

        num_matches = matches_im0.shape[0]
        print(f'  - Found {num_matches} valid matches.')
        
        if num_matches > n_viz:
            match_idx_to_viz = np.round(np.linspace(0, num_matches - 1, n_viz)).astype(int)
            viz_matches_im0, viz_matches_im1 = matches_im0[match_idx_to_viz], matches_im1[match_idx_to_viz]

            image_mean = torch.as_tensor([0.5, 0.5, 0.5], device='cpu').reshape(1, 3, 1, 1)
            image_std = torch.as_tensor([0.5, 0.5, 0.5], device='cpu').reshape(1, 3, 1, 1)

            viz_imgs = []
            for k, view in enumerate([view1, view2]):
                rgb_tensor = view['img'] * image_std + image_mean
                viz_imgs.append(rgb_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy())

            H0_viz, W0_viz, H1_viz, W1_viz = *viz_imgs[0].shape[:2], *viz_imgs[1].shape[:2]
            img0 = np.pad(viz_imgs[0], ((0, max(H1_viz - H0_viz, 0)), (0, 0), (0, 0)), 'constant', constant_values=0)
            img1 = np.pad(viz_imgs[1], ((0, max(H0_viz - H1_viz, 0)), (0, 0), (0, 0)), 'constant', constant_values=0)
            img = np.concatenate((img0, img1), axis=1)
            pl.figure()
            pl.imshow(img)
            cmap = pl.get_cmap('jet')
            for k in range(n_viz):
                (x0, y0), (x1, y1) = viz_matches_im0[k].T, viz_matches_im1[k].T
                pl.plot([x0, x1 + W0_viz], [y0, y1], '-+', color=cmap(k / (n_viz - 1)), scalex=False, scaley=False)
            pl.show(block=True)
            
        if num_matches == 0:
            continue
        
        print("  - Triangulating 3D points...")
        
        # ================================================================= #
        # ### 여기가 수정된 부분입니다 ###
        # sfm.triangulatePoints 함수는 각 뷰의 포인트를 (2, N) 형태로 기대합니다.
        # 기존의 (N, 2) 형태인 matches_im0과 matches_im1을 .T를 사용해 전치합니다.
        pts2d_pair = np.array([matches_im0.T, matches_im1.T], dtype=np.float64)
        # ================================================================= #

        Ps_pair = [Ps[i], Ps[j]]
        point3d_mat = cv2.sfm.triangulatePoints(pts2d_pair, Ps_pair)
        points_3d_pair = point3d_mat.T

        h_ref, w_ref, _ = images_cv[i].shape
        for k in range(num_matches):
            x, y = map(int, matches_im0[k])
            if 0 <= x < w_ref and 0 <= y < h_ref:
                all_colors.append(images_cv[i][y, x][::-1])
                all_points_3d.append(points_3d_pair[k])
    
    if not all_points_3d:
        print("경고: 유효한 3D 포인트가 하나도 생성되지 않았습니다.")
        return np.array([]), np.array([])

    return np.array(all_points_3d), np.array(all_colors)

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

    print("[3] MASt3R 매칭 및 2-view 삼각측량 시작...")
    all_points_3d, all_colors = extract_and_triangulate_pairs(image_paths, images_cv, Ps, mast3r_model, device)
    
    if all_points_3d.size == 0:
        print("최종적으로 복원된 3D 포인트가 없습니다. 프로그램을 종료합니다.")
        return
        
    print(f"\n[4] 총 {len(all_points_3d)}개의 3D 포인트 복원 완료.")

    print("[5] 3D 포인트 클라우드 시각화 중...")
    visualize_point_cloud(all_points_3d, all_colors, Ps)

if __name__ == "__main__":
    main()