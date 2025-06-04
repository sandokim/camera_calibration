import json
import numpy as np
import glob
import os
import cv2 as cv
import matplotlib.pyplot as plt

def normalize_vector(v):
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
    x_dir = normalize_vector(rotation[:, 0])
    y_dir = normalize_vector(rotation[:, 1])
    z_dir = normalize_vector(rotation[:, 2])

    ax.quiver(*origin, *x_dir, color=color[0], arrow_length_ratio=0.1, label=f'{label} X-axis')
    ax.quiver(*origin, *y_dir, color=color[1], arrow_length_ratio=0.1, label=f'{label} Y-axis')
    ax.quiver(*origin, *z_dir, color=color[2], arrow_length_ratio=0.1, label=f'{label} Z-axis')

transforms_path = "dataset/nerf_synthetic/lego/transforms_train.json"
with open(transforms_path, "r") as json_file:
    transforms_json = json.load(json_file)

poses_transformations = []
for i in range(len(transforms_json["frames"])): # poses_npy.shape (34, 17)
    pose = np.array(transforms_json["frames"][i]["transform_matrix"])
    poses_transformations.append(pose)

# Create a new 3D plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim([-10, 10])
ax.set_ylim([-10, 10])
ax.set_zlim([-10, 10])

wcs = np.eye(4)
plot_axes(ax, wcs, label=f'wcs', color=['r', 'g', 'b'])

# c2w_transformations = c2w_transformations[4:5] + c2w_transformations[7:8]
for i, pose in enumerate(poses_transformations):
    plot_axes(ax, pose, label=f'pose {i+1}', color=['crimson', 'limegreen', 'dodgerblue'])

# Set axis labels and add a legend
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.legend()

# Display the plot
plt.show()