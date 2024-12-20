import json
import os
import argparse
from pymatgen.core import Structure
import glob
import sys

def parse_arguments():
    """
    Parses command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Generate POSCAR files from JSON files containing 2D structures."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Path to the directory containing the input JSON files.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="POSCAR_files",
        help="Directory to save the generated POSCAR files. Defaults to 'POSCAR_files'.",
    )
    parser.add_argument(
        "-f",
        "--filename_prefix",
        type=str,
        default="POSCAR_",
        help="Prefix for the POSCAR filenames. Defaults to 'POSCAR_'.",
    )
    return parser.parse_args()

def load_json(file_path):
    """
    Loads JSON data from a file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict: Parsed JSON data.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        print(f"Successfully loaded JSON data from '{file_path}'.")
        return data
    except Exception as e:
        print(f"Error loading JSON file '{file_path}': {e}")
        return None  # Return None instead of exiting

def create_output_directory(directory):
    """
    Creates the output directory if it does not exist.

    Args:
        directory (str): Path to the output directory.
    """
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            print(f"Created output directory '{directory}'.")
        except Exception as e:
            print(f"Error creating directory '{directory}': {e}")
            sys.exit(1)
    else:
        print(f"Output directory '{directory}' already exists.")

def generate_poscar(structure, filename):
    """
    Generates a POSCAR file from a pymatgen Structure object.

    Args:
        structure (Structure): pymatgen Structure object.
        filename (str): Path to save the POSCAR file.
    """
    try:
        structure.to(fmt="poscar", filename=filename)
        print(f"POSCAR file written to '{filename}'.")
    except Exception as e:
        print(f"Error writing POSCAR file '{filename}': {e}")

def sanitize_filename(name):
    """
    Sanitizes the filename by removing or replacing invalid characters.

    Args:
        name (str): Original filename.

    Returns:
        str: Sanitized filename.
    """
    return "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in name)

def main():
    # Parse command-line arguments
    args = parse_arguments()
    input_dir = args.input
    output_dir = args.output
    filename_prefix = args.filename_prefix

    # Create output directory
    create_output_directory(output_dir)

    # Iterate over input directory
    pattern = os.path.join(input_dir, "*.json")
    json_files = sorted(glob.glob(pattern))

    if not json_files:
        print(f"No JSON files found in directory '{input_dir}'.")
        sys.exit(1)

    for file_index, file_path in enumerate(json_files):
        print(f"\nProcessing file {file_index}: '{file_path}'")

        # Load JSON data
        data = load_json(file_path)
        if data is None:
            continue  # Skip this file if loading failed

        # Iterate over the top-level keys in the JSON data
        for top_key in data:
            print(f"Processing top-level key: '{top_key}'")
            entries = data[top_key]
            if not entries:
                print(f"No entries found under key '{top_key}'. Skipping.")
                continue

            for entry_index, entry in enumerate(entries):
                # Each entry is a dictionary with keys like "ENAUG", "ENMAX", etc.
                steps = entry.get('steps', [])
                if not steps:
                    print(f"No 'steps' found in entry {entry_index} under key '{top_key}'. Skipping.")
                    continue

                for step_index, step in enumerate(steps):
                    structure_dict = step.get('structure')
                    if not structure_dict:
                        print(f"No 'structure' found in step {step_index} of entry {entry_index} under key '{top_key}'. Skipping.")
                        continue

                    try:
                        # Reconstruct the Structure object
                        structure = Structure.from_dict(structure_dict)
                    except Exception as e:
                        print(f"Error reconstructing Structure for step {step_index} of entry {entry_index} under key '{top_key}': {e}")
                        continue

                    # Generate POSCAR filename
                    sanitized_top_key = sanitize_filename(top_key) or "key_empty"
                    base_filename = os.path.basename(file_path)
                    sanitized_base_filename = sanitize_filename(os.path.splitext(base_filename)[0])
                    poscar_filename = f"{filename_prefix}{sanitized_base_filename}_{sanitized_top_key}_entry{entry_index}_step{step_index}.vasp"

                    # Full path for the POSCAR file
                    poscar_path = os.path.join(output_dir, poscar_filename)

                    # Generate the POSCAR file
                    generate_poscar(structure, poscar_path)

    print("\nAll POSCAR files have been generated.")

if __name__ == "__main__":
    main()
