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
    ax.set_title(f"MASt3R + Multi-View Triangulation")
    
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
        
        '''
        To do: Multi-view correspondences 관계 2D-2D-2D.. 대응점 관계 찾아서 cv2.sfm.triangulatePoints에 입력하기
        - cv2.sfm.triangulatePoints(InputArrrayOfArrays points2d, InputArrayOfArrays projection_matrices, OutputArray points3d)
            - 제공된 코드의 핵심은 2개 뷰(2-view)의 경우와 3개 이상의 뷰(N-view)의 경우를 나누어 처리하며, 두 경우 모두 DLT(Direct Linear Transformation) 원리를 기반으로 3D 좌표를 계산한다는 점입니다.
            - 뷰의 개수(nviews)가 정확히 2개일 경우, triangulateDLT 함수를 각 점 쌍에 대해 호출합니다.
                - 2-뷰의 경우(triangulateDLT): 각 대응점 쌍으로부터 4개의 선형 방정식을 만들어 AX=0 시스템을 구성하고, SVD를 이용해 X를 직접 풉니다. 이는 책 12.2절에 기술된 표준 DLT 방법과 정확히 일치합니다. 
            - 뷰의 개수가 2개보다 많을 경우, triangulateNViews 함수를 각 점 트랙에 대해 호출합니다.
                - 다중 뷰의 경우(triangulateNViews): 3D 점 X와 각 뷰의 깊이 스케일 λi를 모두 미지수로 두는 더 큰 선형 시스템을 구성합니다. SVD를 통해 이 시스템을 푼 뒤, 3D 점에 해당하는 부분만 추출하여 최종 결과를 얻습니다. 이 방법은 모든 뷰의 정보를 동시에 활용하여 더 안정적이고 정확한 결과를 얻을 수 있습니다.

            - 다중 뷰(3개 이상)에 대해 이 함수를 호출하기 위해 필요한 입력은 `points2d`와 `projection_matrices` 두 가지입니다.
                - points2d: 2D 대응점 데이터
                - 이 매개변수는 여러 뷰에 걸쳐 추적된 2D 점들의 집합입니다.
                - 예를 들어, 3개의 뷰에서 100개의 점을 삼각측량한다면:
                    - points2d는 3개의 Mat 객체를 담고 있는 vector가 됩니다.
                    - 각 Mat은 2x100 크기를 가집니다.
                    - points2d[0].col(5)는 첫 번째 뷰의 6번째 점의 (x,y) 좌표입니다.
                    - points2d[1].col(5)는 두 번째 뷰의 6번째 점의 (x,y) 좌표입니다.
                    - points2d[2].col(5)는 세 번째 뷰의 6번째 점의 (x,y) 좌표입니다.
                    - 이 세 점 points2d[0].col(5), points2d[1].col(5), points2d[2].col(5)는 모두 동일한 3D 공간상의 한 점에서 투영된 것이어야 합니다.
                - `projection_matrices`: 투영 행렬 데이터
                - 이 매개변수는 각 뷰에 해당하는 카메라의 투영 행렬(카메라 행렬) 집합입니다.
                - 벡터의 크기는 전체 뷰의 개수 m으로, points2d 벡터의 크기와 정확히 일치해야 합니다.
                - 벡터의 각 요소인 cv::Mat 객체는 3x4 크기를 가집니다.
                - 모든 투영 행렬 P_i는 반드시 동일한 월드 좌표계(world coordinate system)를 기준으로 표현되어야 합니다.
                - 이 행렬들은 일반적으로 사전 단계에서 계산됩니다. 예를 들어, Fundamental Matrix 또는 Trifocal Tensor를 계산한 뒤 이로부터 카메라 행렬을 복원하거나(projective reconstruction), 번들 조정(bundle adjustment)을 통해 얻어진 결과물일 수 있습니다.
                - 각기 다른 시점에 독립적으로 캘리브레이션된 카메라 행렬들을 그대로 사용하면, 각 카메라가 자신만의 월드 좌표계를 가지므로 올바른 삼각측량이 불가능합니다.
        '''
        print("  - Triangulating 3D points...")
        
        point3d_mat = cv2.sfm.triangulatePoints(pts2d_pair, Ps_pair)
        points_3d = point3d_mat.T

        h_ref, w_ref, _ = images_cv[i].shape
        for k in range(num_matches):
            x, y = map(int, matches_im0[k])
            if 0 <= x < w_ref and 0 <= y < h_ref:
                all_colors.append(images_cv[i][y, x][::-1])
                all_points_3d.append(points_3d[k])
    
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

    print("[3] MASt3R 매칭 및 multi-view 삼각측량 시작...")
    all_points_3d, all_colors = extract_and_triangulate_pairs(image_paths, images_cv, Ps, mast3r_model, device)
    
    if all_points_3d.size == 0:
        print("최종적으로 복원된 3D 포인트가 없습니다. 프로그램을 종료합니다.")
        return
        
    print(f"\n[4] 총 {len(all_points_3d)}개의 3D 포인트 복원 완료.")

    print("[5] 3D 포인트 클라우드 시각화 중...")
    visualize_point_cloud(all_points_3d, all_colors, Ps)

if __name__ == "__main__":
    main()