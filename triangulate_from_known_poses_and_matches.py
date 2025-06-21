import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from typing import List
import cv2
import torch
from dkm import DKMv3_outdoor
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
dkm_model = DKMv3_outdoor(device=device)
print(f"DKM model loaded on {device}")

'''
dkm으로 matches를 2-view이상에서 찾아서 cv2.sfm.triangulatePoints(pts2d, Ps, pts_3d) 를 수행하자
https://github.com/Parskatt/DKM/blob/main/demo/demo_match.py

from PIL import Image
import torch
import torch.nn.functional as F
import numpy as np
from dkm.utils.utils import tensor_to_pil

from dkm import DKMv3_outdoor

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--im_A_path", default="assets/sacre_coeur_A.jpg", type=str)
    parser.add_argument("--im_B_path", default="assets/sacre_coeur_B.jpg", type=str)
    parser.add_argument("--save_path", default="demo/dkmv3_warp_sacre_coeur.jpg", type=str)

    args, _ = parser.parse_known_args()
    im1_path = args.im_A_path
    im2_path = args.im_B_path
    save_path = args.save_path

    # Create model
    dkm_model = DKMv3_outdoor(device=device)

    H, W = 864, 1152

    im1 = Image.open(im1_path).resize((W, H))
    im2 = Image.open(im2_path).resize((W, H))

    # Match
    warp, certainty = dkm_model.match(im1_path, im2_path, device=device)
    # Sampling not needed, but can be done with model.sample(warp, certainty)
    dkm_model.sample(warp, certainty)
    x1 = (torch.tensor(np.array(im1)) / 255).to(device).permute(2, 0, 1)
    x2 = (torch.tensor(np.array(im2)) / 255).to(device).permute(2, 0, 1)

    im2_transfer_rgb = F.grid_sample(
    x2[None], warp[:,:W, 2:][None], mode="bilinear", align_corners=False
    )[0]
    im1_transfer_rgb = F.grid_sample(
    x1[None], warp[:, W:, :2][None], mode="bilinear", align_corners=False
    )[0]
    warp_im = torch.cat((im2_transfer_rgb,im1_transfer_rgb),dim=2)
    white_im = torch.ones((H,2*W),device=device)
    vis_im = certainty * warp_im + (1 - certainty) * white_im
    tensor_to_pil(vis_im, unnormalize=False).save(save_path)
'''

# ------------------ 설정 ------------------
BASE_DIR = "multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface"
IMAGE_DIR = os.path.join(BASE_DIR, "images")
CAMERAS = ['cam0', 'cam1', 'cam2', 'cam3']
INTRINSICS_PATHS = [os.path.join(IMAGE_DIR, cam, "intrinsics.json") for cam in CAMERAS]
EXTRINSICS_PATH = os.path.join(BASE_DIR, "extrinsics.json")

# ------------------ 이미지 로드 ------------------
def load_images() -> (List[np.ndarray], List[str]):
    image_paths = [os.path.join(IMAGE_DIR, cam, os.listdir(os.path.join(IMAGE_DIR, cam))[0]) for cam in CAMERAS]
    images = []
    for p in image_paths:
        img = cv2.imread(p)
        if img is None:
            raise ValueError(f"이미지 로드 실패: {p}")
        images.append(img)
    return images, image_paths

# ------------------ Intrinsics / Extrinsics 로드 ------------------
def load_intrinsics() -> List[np.ndarray]:
    Ks = []
    for path in INTRINSICS_PATHS:
        with open(path, 'r') as f:
            data = json.load(f)
            Ks.append(np.array(data["mtx"]))
    return Ks

def load_extrinsics(image_rel_paths: List[str]) -> List[np.ndarray]:
    with open(EXTRINSICS_PATH, 'r') as f:
        data = json.load(f)

    Ps = []
    for rel_path in image_rel_paths:
        rel_key = os.path.relpath(rel_path, IMAGE_DIR).replace('\\', '/')
        if rel_key not in data:
            raise ValueError(f"{rel_key} not found in extrinsics.json")
        T = np.array(data[rel_key])
        P = T[:3, :]
        Ps.append(P)
    return Ps

# ------------------ 특징 추출 및 매칭 ------------------
def extract_sift_tracks(images: List[np.ndarray]):
    sift = cv2.SIFT_create()
    keypoints, descriptors = [], []

    for img in images:
        kp, des = sift.detectAndCompute(img, None)
        keypoints.append(kp)
        descriptors.append(des)

    n_views = len(images)
    tracks = defaultdict(lambda: [None] * n_views)
    bf = cv2.BFMatcher()
    track_id = 0

    for i in range(n_views):
        for j in range(i + 1, n_views):
            if descriptors[i] is None or descriptors[j] is None:
                continue
            matches = bf.knnMatch(descriptors[i], descriptors[j], k=2)
            for m, n in matches:
                if m.distance < 0.75 * n.distance:
                    pt_i = keypoints[i][m.queryIdx].pt
                    pt_j = keypoints[j][m.trainIdx].pt
                    tracks[track_id][i] = pt_i
                    tracks[track_id][j] = pt_j
                    track_id += 1
    return tracks

# ------------------ Triangulation ------------------
def triangulate_track(track: List, projection_matrices: List[np.ndarray], images: List[np.ndarray]) -> (np.ndarray, np.ndarray):
    views = [(i, pt) for i, pt in enumerate(track) if pt is not None]
    if len(views) < 2:
        return None, None

    pts2d = np.array([pt for _, pt in views], dtype=np.float64).T  # (2, N)
    Ps = [projection_matrices[i] for i, _ in views]

    pts_3d = np.zeros((3, 1))
    cv2.sfm.triangulatePoints(pts2d, Ps, pts_3d)
    point3d = pts_3d[:, 0]

    # 첫 번째 관측 이미지에서 색 가져오기
    i0, pt0 = views[0]
    x, y = map(int, pt0)
    color = images[i0][y, x][::-1]  # BGR → RGB

    return point3d, color

# ------------------ 시각화 ------------------
def visualize_point_cloud(points_3d, colors):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(points_3d[:, 0], points_3d[:, 1], points_3d[:, 2], c=colors / 255.0, s=1)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Triangulated 3D Points with Color")
    plt.show()

# ------------------ 전체 파이프라인 ------------------
def main():
    print("[1] 이미지 로드")
    images, image_paths = load_images()

    print("[2] Intrinsics / Extrinsics 로드")
    Ks = load_intrinsics()
    Ps_raw = load_extrinsics(image_paths)
    Ps = [K @ P for K, P in zip(Ks, Ps_raw)]

    print("[3] 특징 추출 및 트랙 생성")
    tracks = extract_sift_tracks(images)
    print(f"    → 트랙 수: {len(tracks)}")

    points_3d = []
    colors = []

    for track in tracks.values():
        if sum(p is not None for p in track) >= 2:
            pt3d, color = triangulate_track(track, Ps, images)
            if pt3d is not None:
                points_3d.append(pt3d)
                colors.append(color)

    if not points_3d:
        print("    → 유효한 3D 포인트 없음")
        return

    points_3d = np.array(points_3d)
    colors = np.array(colors)
    print(f"[4] Triangulated points: {len(points_3d)}개")

    print("[5] 시각화")
    visualize_point_cloud(points_3d, colors)

if __name__ == "__main__":
    main()
