from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Open the image file
file_path = 'r_59.png'
image = Image.open(file_path)

# Check if the image is RGBA
is_rgba = image.mode == 'RGBA'

if is_rgba:
    # Convert image to numpy array
    image_array = np.array(image)
    # Extract the alpha channel
    alpha_channel = image_array[:, :, 3]
    
    # Count the occurrences of each alpha value
    unique, counts = np.unique(alpha_channel, return_counts=True)
    
    # Print alpha values and counts
    for u, c in zip(unique, counts):
        print(f"Alpha Value: {u}, Count: {c}")
    
    # Visualize the alpha channel
    plt.figure(figsize=(8, 8))
    plt.imshow(alpha_channel, cmap='gray')
    plt.title('Alpha Channel Visualization')
    plt.axis('off')
    plt.show()
else:
    print("The image is not in RGBA format.")
