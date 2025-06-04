import numpy as np
import open3d as o3d
import os

# 스테레오 캘리브레이션으로부터 얻은 변환 매트릭스 (예제)
# 여기서는 4x4 변환 매트릭스를 사용합니다. 마지막 행은 [0, 0, 0, 1]입니다.
transform_matrix = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 10],
    [0, 0, 0, 1]
])
# transform_matrix = np.eye(4)

pcd = o3d.io.read_point_cloud(os.getcwd() + "/points3d.ply")
points = np.asarray(pcd.points)

# 동차 좌표계를 사용하여 변환을 수행하기 위해 각 포인트에 1을 추가합니다.
homogeneous_points = np.hstack((points, np.ones((points.shape[0], 1))))

transformed_points = np.dot(homogeneous_points, transform_matrix.T)

# 변환된 좌표를 사용하여 새로운 포인트 클라우드 생성
transformed_pcd = o3d.geometry.PointCloud()
transformed_pcd.points = o3d.utility.Vector3dVector(transformed_points[:, :3])

# 변환된 포인트 클라우드 저장 또는 시각화
# 저장
o3d.io.write_point_cloud(os.getcwd() + "/points3d_transformed.ply", transformed_pcd)

# 시각화
o3d.visualization.draw_geometries([transformed_pcd])
