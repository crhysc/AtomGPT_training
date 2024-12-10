import json
import os
import argparse
from pymatgen.core import Structure
from pymatgen.core.structure import Structure
from pymatgen.core.lattice import Lattice
import glob

def parse_arguments():
    """
    Parses command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Generate POSCAR files from a JSON file containing pymatgen entries."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Path to the directory containing the input JSON files (e.g., decompressed_000.json).",
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
        exit(1)

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
            exit(1)
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

    # Iterate over input directory
    pattern = os.path.join(input_dir, "*.json")
    for index, file_path in enumerate(sorted(glob.glob(pattern))):
        
        print(f"Processing file {index}: {file_path}")

        # Make text file for each json to see the speed it progresses
        with open(f"completed{index}.txt", "w") as file:
            pass

        # Load JSON data
        data = load_json(file_path)

        # Create output directory
        create_output_directory(output_dir)

        # Extract entries
        entries = data.get('entries', [])
        if not entries:
            print("No 'entries' found in the JSON file.")
            exit(1)

        print(f"Found {len(entries)} entries in the JSON file.")

        # Iterate over entries and generate POSCAR files
        for idx, entry in enumerate(entries, start=1):
            print(f"\nProcessing entry {idx}/{len(entries)}...")

            # Extract the structure dictionary
            structure_dict = entry.get('structure')
            if not structure_dict:
                print(f"Entry {idx} does not contain a 'structure' key. Skipping.")
                continue

            try:
                # Reconstruct the Structure object using pymatgen
                structure = Structure.from_dict(structure_dict)
            except Exception as e:
                    print(f"Error reconstructing Structure for entry {idx}: {e}")
                    continue

            # Determine a unique identifier for the POSCAR filename
            # Prefer 'mat_id' if available, else use the entry index
            mat_id = entry.get('data', {}).get('mat_id', f'entry_{idx}')
            if not mat_id:
                mat_id = f'entry_{idx}'
            sanitized_mat_id = sanitize_filename(mat_id)
            poscar_filename = f"{filename_prefix}_jsonNum_{index}_entryNum{idx}_{sanitized_mat_id}.vasp"
            print(poscar_filename)

            # Full path for the POSCAR file
            poscar_path = os.path.join(output_dir, poscar_filename)

            # Generate the POSCAR file
            generate_poscar(structure, poscar_path)
            
        print("\nAll POSCAR files have been generated.")

if __name__ == "__main__":
    main()
