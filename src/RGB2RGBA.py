from PIL import Image
import os

# Define paths
mask_path = './dataset/d435_180deg@15/mask'
rgb_path = './dataset/d435_180deg@15/0deg_Undistorted'
output_path = './dataset/d435_180deg@15/rgba_images'

# Create output directory if it doesn't exist
os.makedirs(output_path, exist_ok=True)

# List of mask and RGB files (assuming they are named similarly)
mask_files = sorted([f for f in os.listdir(mask_path) if f.endswith('.png')])
rgb_files = sorted([f for f in os.listdir(rgb_path) if f.endswith('.png')])

# Check if the number of masks and RGB images match
if len(mask_files) != len(rgb_files):
    print("The number of mask files and RGB files do not match.")
else:
    for mask_file, rgb_file in zip(mask_files, rgb_files):
        mask = Image.open(os.path.join(mask_path, mask_file)).convert('L')  # Open mask and convert to grayscale
        rgb = Image.open(os.path.join(rgb_path, rgb_file)).convert('RGB')   # Open RGB image and convert to RGB
        
        # Create an RGBA image from the RGB image
        rgba = rgb.copy()
        rgba.putalpha(mask)

        # Save the RGBA image
        output_file = os.path.join(output_path, rgb_files)
        rgba.save(output_file, 'PNG')

    print("RGBA images have been created successfully.")

