import json
import numpy as np
import glob
import os
import cv2 as cv
import matplotlib.pyplot as plt

def poses_avg(poses):

    hwf = poses[0, :3, -1:]

    center = poses[:, :3, 3].mean(0)
    vec2 = normalize(poses[:, :3, 2].sum(0))
    up = poses[:, :3, 1].sum(0)
    c2w = np.concatenate([viewmatrix(vec2, up, center), hwf], 1)
    
    return c2w

def viewmatrix(z, up, pos):
    vec2 = normalize(z)
    vec1_avg = up
    vec0 = normalize(np.cross(vec1_avg, vec2))
    vec1 = normalize(np.cross(vec2, vec0))
    m = np.stack([vec0, vec1, vec2, pos], 1)
    return m

def normalize(v):
    """Normalize a vector to have a length of 1."""
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

def plot_axes(ax, matrix, label='', color=['r', 'g', 'b']):
    """
    Plot the X, Y, Z axes of a coordinate system given an origin and transformation matrix,
    with normalized axes length.

    :param ax: The 3D axis to plot on.
    :param matrix: The transformation matrix representing the coordinate system.
    :param length: The length of the axes.
    :param label: Label for the coordinate system.
    """
    # Extract the rotation part of the transformation matrix
    origin = matrix[:3, 3]
    rotation = matrix[:3, :3]

    # Scale and normalize the axes
    x_dir = normalize(rotation[:, 0])
    y_dir = normalize(rotation[:, 1])
    z_dir = normalize(rotation[:, 2])

    ax.quiver(*origin, *x_dir, color=color[0], arrow_length_ratio=0.1, label=f'{label} X-axis')
    ax.quiver(*origin, *y_dir, color=color[1], arrow_length_ratio=0.1, label=f'{label} Y-axis')
    ax.quiver(*origin, *z_dir, color=color[2], arrow_length_ratio=0.1, label=f'{label} Z-axis')

poses_arr = np.load("dataset/nerf_llff_data/flower/poses_bounds.npy")
poses = poses_arr[:, :-2].reshape([-1, 3, 5])
'''
https://github.com/kwea123/nerf_pl/issues/58 
Btw, the translation vector has nothing to do here, since it's the camera's position in world coordinate, so it won't change. Remember that we are changing how is the camera rotated w.r.t. the world only.
# Original poses has rotation in form "down right back", change to "right up back"
# poses = np.concatenate([poses[..., 1:2], -poses[..., :1], poses[..., 2:4]], -1)
'''
poses_transformations = []
for i in range(poses.shape[0]): # poses_npy.shape (34, 17)
    pose = poses[i, :3, :4]
    pose_4x4 = np.eye(4)
    pose_4x4[:3, :4] = pose
    poses_transformations.append(pose_4x4)
    
# Create a new 3D plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim([-7, 7])
ax.set_ylim([-7, 7])
ax.set_zlim([-7, 7])

wcs = poses_avg(np.array(poses_transformations))
plot_axes(ax, wcs, label=f'wcs', color=['r', 'g', 'b'])

for i, pose in enumerate(poses_transformations):
    plot_axes(ax, pose, label=f'pose {i+1}', color=['magenta', 'purple', 'cyan']) # color=['magenta', 'purple', 'cyan']

# Set axis labels and add a legend
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.legend()

# Display the plot
plt.show()