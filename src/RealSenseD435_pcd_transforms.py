import numpy as np
import open3d as o3d

# PLY 파일 로드
pcd = o3d.io.read_point_cloud("dataset/d435@180deg/RealSenseD435_face_depth_mesh.ply")

# numpy 배열로 포인트 클라우드 데이터 가져오기
points = np.asarray(pcd.points)
normals = np.asarray(pcd.normals)
colors = np.asarray(pcd.colors)
'''
right up, back --> right, down, forward
Y와 Z 좌표의 방향을 반대로 (부호 반전) 
단, colors는 일반적으로 0~1 사이의 값을 가지며, 방향성이 없기 때문에, 좌표계의 변환과는 무관하게 처리한다.
'''
points[:, 1] = -points[:, 1]  # Y 좌표 부호 반전
points[:, 2] = -points[:, 2]  # Z 좌표 부호 반전

normals[:, 1] = -normals[:, 1]  # Y 좌표 부호 반전
normals[:, 2] = -normals[:, 2]  # Z 좌표 부호 반전

# 반전된 포인트를 새로운 PCD 객체에 할당하고 저장 --> right, up, back --> right, down, forward
axes_fliped_pcd = o3d.geometry.PointCloud()
axes_fliped_pcd.points = o3d.utility.Vector3dVector(points)
axes_fliped_pcd.normals = o3d.utility.Vector3dVector(normals)
axes_fliped_pcd.colors = o3d.utility.Vector3dVector(colors)
o3d.io.write_point_cloud("dataset/d435@180deg/points3d.ply", axes_fliped_pcd)

'''
remove bg pcd manually 
'''
# 배경 제거를 위한 범위 정의 (예시)
min_bound = np.array([-0.2, -0.2, 0.0])  # 최소 범위
max_bound = np.array([0.2, 0.2, 0.5])   # 최대 범위

# 범위 필터링
filtered_indices = np.all((points >= min_bound) & (points <= max_bound), axis=1)
filtered_points = points[filtered_indices]
filtered_normals = normals[filtered_indices]
filtered_colors = colors[filtered_indices]

# 필터링된 포인트 클라우드를 새로운 PCD 객체에 할당
filtered_pcd = o3d.geometry.PointCloud()
filtered_pcd.points = o3d.utility.Vector3dVector(filtered_points)
filtered_pcd.normals = o3d.utility.Vector3dVector(filtered_normals)
filtered_pcd.colors = o3d.utility.Vector3dVector(filtered_colors)
o3d.io.write_point_cloud("dataset/d435@180deg/filtered_points3d.ply", filtered_pcd)

'''
RotationLeftRGB, TranslationLeftRGB 정의 --> from RGB to Left transform
'''
R = np.array([[0.999835, -0.0144807, 0.0109438],
              [0.0145299, 0.999885, -0.00443285],
              [-0.0108784, 0.00459113, 0.9993]])
T = np.array([15.371313, -0.0011960, 0.853173])

# 4x4 transformation matrix 생성
transformation_matrix = np.eye(4)  # Create a 4x4 identity matrix
transformation_matrix[:3, :3] = R
transformation_matrix[:3, 3] = T

# Inverse transformation matrix 계산 --> from Left to RGB transform
inverse_transformation_matrix = np.linalg.inv(transformation_matrix)

# 포인트 클라우드에 역변환 적용
homogeneous_points = np.hstack([points, np.ones((points.shape[0], 1))])  # Add a column of ones for homogeneous coordinates
transformed_points = np.dot(homogeneous_points, inverse_transformation_matrix.T)[:, :3]

# 변환된 포인트 클라우드를 새로운 PCD 객체에 할당
transformed_pcd = o3d.geometry.PointCloud()
transformed_pcd.points = o3d.utility.Vector3dVector(transformed_points)

# 결과 PLY 파일로 저장
o3d.io.write_point_cloud("dataset/d435@180deg/RealSenseD435_face_depth_mesh_RGB_coordinate.ply", transformed_pcd)

print("Transformed PLY file has been saved!")
