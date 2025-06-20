"""
This script performs triangulation of 3D points using:
- Pre-computed camera poses from PnP
- A variety of feature-matching strategies (e.g., SIFT, LoFTR, D2-Net, etc.)

For each matching method, only correspondences with ≥ 2 views are triangulated.

The goal is to evaluate how different matching strategies affect:
- Number of triangulated points
- Geometric consistency
- Bundle Adjustment results
"""

import os, sys
import json
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from typing import List, Tuple
# DLL 경로
os.add_dll_directory("C:/Users/maila/opencv/build/bin/Release")
# .pyd 경로
sys.path.append("C:/Users/maila/opencv/build/lib/python3/Release")
from cv2 import sfm

# ------------------ 설정 ------------------
IMAGE_DIR = "./images"
INTRINSICS_PATH = "./intrinsics.json"
EXTRINSICS_PATH = "./extrinsics.json"

# ------------------ Matching Method Wrappers ------------------
def dummy_matches(images):
    # 각 뷰에 대해 대응되는 2D 점 좌표들을 numpy 배열로 리턴
    pts_per_view = [
        np.array([[100, 100], [120, 120], [140, 140]], dtype=np.float64).T,  # view 0
        np.array([[102, 98], [122, 118], [142, 138]], dtype=np.float64).T,   # view 1
        np.array([[98, 103], [118, 123], [138, 143]], dtype=np.float64).T    # view 2
    ]
    return pts_per_view

def extract_matches_dkm(images):
    return dummy_matches(images)

def extract_matches_mast3r(images):
    return dummy_matches(images)

def extract_matches_sift(images: List[np.ndarray]):
    detector = cv2.SIFT_create()
    keypoints_list = []
    descriptors_list = []
    for img in images:
        kp, des = detector.detectAndCompute(img, None)
        keypoints_list.append(kp)
        descriptors_list.append(des)

    matcher = cv2.BFMatcher()
    match_pairs = []
    for i in range(len(descriptors_list)):
        for j in range(i + 1, len(descriptors_list)):
            matches = matcher.knnMatch(descriptors_list[i], descriptors_list[j], k=2)
            good_matches = [(m.queryIdx, m.trainIdx) for m, n in matches if m.distance < 0.75 * n.distance]
            match_pairs.append((i, j, good_matches))
    return match_pairs

# ------------------ 전체 Feature + Matching Pipeline ------------------
def extract_and_match_features(images: List[np.ndarray], method: str = "sift"):
    if method == "sift":
        return extract_matches_sift(images)
    elif method == "dkm":
        return extract_matches_dkm(images)
    elif method == "mast3r":
        return extract_matches_mast3r(images)
    else:
        raise ValueError("Unsupported feature extraction method")

# ------------------ Triangulation ------------------
def triangulate_multiview_with_sfm(points2d_per_view, projection_matrices):
    assert len(points2d_per_view) == len(projection_matrices), "Number of 2D point sets must match number of views"
    n_views = len(points2d_per_view)
    n_points = points2d_per_view[0].shape[1]

    # Input to sfm.triangulatePoints: list of 2xN, list of 3x4
    pts_3d = np.zeros((3, n_points))
    sfm.triangulatePoints(points2d_per_view, projection_matrices, pts_3d)
    return pts_3d.T

# ------------------ Visualization ------------------
def visualize_point_cloud(points_3d):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(points_3d[:, 0], points_3d[:, 1], points_3d[:, 2], s=1, c='b')
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Triangulated 3D Points")
    plt.show()

# ------------------ Main Pipeline ------------------
def main():
    with open(INTRINSICS_PATH, 'r') as f:
        intrinsics = json.load(f)
    K = np.array(intrinsics["mtx"])

    with open(EXTRINSICS_PATH, 'r') as f:
        extrinsics = json.load(f)

    images = []
    image_names = sorted(os.listdir(IMAGE_DIR))
    for name in image_names:
        img = cv2.imread(os.path.join(IMAGE_DIR, name))
        if img is None:
            continue
        images.append(img)

    projection_matrices = []
    for name in image_names:
        if name not in extrinsics:
            raise ValueError(f"{name} not found in extrinsics.json")
        T = np.array(extrinsics[name])
        P = K @ T[:3, :]
        projection_matrices.append(P)

    method = "dkm"  # "sift", "dkm", "mast3r" 중 선택 가능
    matches = extract_and_match_features(images, method=method)

    if method == "sift":
        print("Triangulation with SIFT matches is not implemented in N-view format.")
        return

    points_3d = triangulate_multiview_with_sfm(matches, projection_matrices)

    if points_3d.size > 0:
        visualize_point_cloud(points_3d)
    else:
        print("No 3D points were triangulated.")

if __name__ == "__main__":
    # main()
    print("sfm 모듈:", sfm)
    

