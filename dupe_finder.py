import os
from PIL import Image
from tqdm import tqdm
import numpy as np
import sys
import argparse
import hashlib
from pathlib import Path


def hash_image(image):
    return hashlib.md5(image.tobytes()).hexdigest()

def quick_compare(file1, file2):
    return file1.split("_")[0] == file2.split("_")[0]


def image_hash(image_path):
    image = Image.open(image_path)
    return hash(image.tobytes())

def flipped_image_hash(image_path):
    image = Image.open(image_path)
    flipped_image = image.transpose(Image.FLIP_LEFT_RIGHT)
    return hash(flipped_image.tobytes())

# find dupes function here 
def find_duplicates(input_dir, quick=False):
    image_files = []
    for dirpath, dirnames, filenames in os.walk(input_dir):
        for filename in filenames:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                full_path = os.path.join(dirpath, filename)
                image_files.append(full_path)

    duplicates = []
    image_hashes = {}
    hash_file_path = os.path.join(input_dir, "image_hashes.txt")

    # Read existing hashes from the file
    if os.path.exists(hash_file_path):
        with open(hash_file_path, "r") as hash_file:
            for line in hash_file:
                file_path, hash1, hash2 = line.strip().split(",")
                image_hashes[file_path] = (hash1, hash2)

    print("Indexing image hashes...")
    indexing_progress_bar = tqdm(total=len(image_files), desc="Indexing", position=0, leave=True)

    save_interval = int(len(image_files) * 0.1)  # Save progress every 10%
    if save_interval == 0:
        save_interval = 1

    for i, file1 in enumerate(image_files):
        if file1 not in image_hashes:
            file1_image = Image.open(file1)
            file1_hash = hash_image(file1_image)
            flipped_file1 = file1_image.transpose(Image.FLIP_LEFT_RIGHT)
            flipped_file1_hash = hash_image(flipped_file1)
            image_hashes[file1] = (file1_hash, flipped_file1_hash)

        # Save progress every 10%
        if i % save_interval == 0:
            with open(hash_file_path, "w") as hash_file:
                for file_path, (hash1, hash2) in image_hashes.items():
                    hash_file.write(f"{file_path},{hash1},{hash2}\n")

        indexing_progress_bar.update(1)

    indexing_progress_bar.close()

    print("Comparing images for duplicates...")
    comparing_progress_bar = tqdm(total=len(image_files), desc="Comparing", position=0, leave=True)

    for i, file1 in enumerate(image_files):
        for file2 in image_files[i+1:]:
            if quick:
                if quick_compare(file1, file2):
                    if file2 not in duplicates:
                        duplicates.append(file2)
            else:
                if file2 in image_hashes:
                    if file1_hash == image_hashes[file2][0] or file1_hash == image_hashes[file2][1] or flipped_file1_hash == image_hashes[file2][0] or flipped_file1_hash == image_hashes[file2][1]:
                        if file2 not in duplicates:
                            duplicates.append(file2)
        comparing_progress_bar.update(1)

    comparing_progress_bar.close()

    # Write the final updated hashes to the file
    with open(hash_file_path, "w") as hash_file:
        for file_path, (hash1, hash2) in image_hashes.items():
            hash_file.write(f"{file_path},{hash1},{hash2}\n")

    return duplicates


def move_duplicates(duplicates, input_dir):
    dupe_dir = os.path.join(input_dir, "dupe")
    Path(dupe_dir).mkdir(parents=True, exist_ok=True)

    for dupe in duplicates:
        os.rename(os.path.join(input_dir, dupe), os.path.join(dupe_dir, dupe))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find and move duplicate images")
    parser.add_argument("input_dir", help="Input directory containing images")
    parser.add_argument("--quick", action="store_true", help="Use quick mode to compare images by name")
    args = parser.parse_args()

    duplicates = find_duplicates(args.input_dir, args.quick)
    move_duplicates(duplicates, args.input_dir)