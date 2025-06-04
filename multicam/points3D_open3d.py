import struct
import numpy as np
import open3d as o3d

def read_points3D_bin(path):
    points3D = {}
    with open(path, "rb") as f:
        while True:
            data = f.read(43)  # 1+3*8+3*8+2*4 = 43 bytes per point
            if not data:
                break
            unpacked = struct.unpack("<Q3d3f2I", data[:38])
            point_id = unpacked[0]
            xyz = np.array(unpacked[1:4])
            rgb = np.array(unpacked[4:7], dtype=np.float32)
            error = struct.unpack("<d", data[38:46])[0]
            track_length = struct.unpack("<Q", data[46:54])[0] if len(data) >= 54 else 0
            points3D[point_id] = (xyz, rgb)
    return points3D

def colmap_points3D_to_open3d(points3D):
    xyz = []
    rgb = []
    for v in points3D.values():
        xyz.append(v[0])
        rgb.append(v[1] / 255.0)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.array(xyz))
    pcd.colors = o3d.utility.Vector3dVector(np.array(rgb))
    return pcd

if __name__ == "__main__":
    # points3D.bin 파일 경로를 지정하세요
    path = "C:/Users/Kang/Desktop/multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/images/sparse/0/points3D.bin"
    points3D = read_points3D_bin(path)
    pcd = colmap_points3D_to_open3d(points3D)
    o3d.visualization.draw_geometries([pcd])