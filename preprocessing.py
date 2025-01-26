# -*- coding: utf-8 -*-
"""preprocessing.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1fj1B-d8IgdVOW_DRbRIVyyhexbe2UvGq
"""

!apt-get install -y openslide-tools
!pip install openslide-python

import openslide

from google.colab import drive
drive.mount('/content/drive')

from google.colab import drive
from PIL import Image, ImageDraw
import openslide
import xml.etree.ElementTree as ET
import os
import numpy as np
import random

wsi_path = '/content/drive/MyDrive/cervix_006.svs'
annotation_path = '/content/drive/MyDrive/cervix_006.xml'
output_dir = '/content/drive/MyDrive/output'

# Create subdirectories for tiles and masks
original_dir = os.path.join(output_dir, "original")
mask_dir = os.path.join(output_dir, "masks")
os.makedirs(original_dir, exist_ok=True)
os.makedirs(mask_dir, exist_ok=True)

# Tile settings
tile_size = 256  # Tile size (e.g., 256x256 pixels)
step_size = 256  # Step size for tiling (no overlap)
max_tiles = 10   # Limit the number of output tiles

# Open the WSI
slide = openslide.OpenSlide(wsi_path)
dimensions = slide.dimensions
print(f"Slide dimensions: {dimensions}")

# Parse the annotation XML file
tree = ET.parse(annotation_path)
root = tree.getroot()

# Extract annotation regions
annotations = []
for region in root.findall(".//Region"):
    vertices = region.find("Vertices")
    points = [(int(float(vertex.attrib["X"])), int(float(vertex.attrib["Y"]))) for vertex in vertices.findall("Vertex")]
    annotations.append(points)

# Helper function: Check if tile is empty
def is_tile_empty(tile, threshold=0.8):
    """
    Determine if a tile is mostly background.
    :param tile: PIL Image tile
    :param threshold: Fraction of white pixels to classify as empty (default 80%)
    :return: True if tile is empty, False otherwise
    """
    tile_array = np.array(tile.convert("L"))  # Convert to grayscale
    white_pixels = np.sum(tile_array > 200)  # Count nearly white pixels
    total_pixels = tile_array.size
    return (white_pixels / total_pixels) > threshold

# Iterate through the WSI to extract tiles
valid_tiles = []  # Store valid tiles and their coordinates
for x in range(0, dimensions[0], step_size):
    for y in range(0, dimensions[1], step_size):
        # Extract tile
        tile = slide.read_region((x, y), 0, (tile_size, tile_size))
        tile = tile.convert("RGB")

        # Skip empty tiles
        if is_tile_empty(tile):
            continue

        # Save valid tiles
        valid_tiles.append((tile, x, y))

# Limit to the desired number of tiles
if len(valid_tiles) > max_tiles:
    valid_tiles = random.sample(valid_tiles, max_tiles)

# Process and save tiles and masks
for i, (tile, x, y) in enumerate(valid_tiles):
    # Create a blank mask for annotations
    mask = Image.new("L", (tile_size, tile_size), 0)  # Binary mask: 0 = background, 255 = annotation
    draw = ImageDraw.Draw(mask)

    # Draw annotations onto the mask
    for annotation in annotations:
        # Adjust annotation coordinates relative to the current tile
        annotation_relative = [(px - x, py - y) for px, py in annotation]
        draw.polygon(annotation_relative, outline=255, fill=255)  # Fill the polygon with white (255)

    # Save the tile and corresponding mask
    tile_filename = os.path.join(original_dir, f"tile_{i}.png")
    mask_filename = os.path.join(mask_dir, f"mask_{i}.png")
    tile.save(tile_filename)
    mask.save(mask_filename)

print(f"Tiles and masks have been saved in: {output_dir}")