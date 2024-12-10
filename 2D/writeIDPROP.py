import json
import csv
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
        description="Generate id_prop.csv from JSON files containing 2D structures and energies."
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
        default=".",
        help="Directory to save the generated id_prop.csv file. Defaults to '.'",
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

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    id_prop_path = os.path.join(output_dir, "id_prop.csv")

    # Open the CSV file for writing
    with open(id_prop_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        skipped = 0
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

            base_filename = os.path.basename(file_path)
            sanitized_base_filename = sanitize_filename(os.path.splitext(base_filename)[0])

            # Iterate over the top-level keys in the JSON data
            for top_key in data:
                print(f"Processing top-level key: '{top_key}'")
                entries = data[top_key]
                if not entries:
                    print(f"No entries found under key '{top_key}'. Skipping.")
                    continue

                sanitized_top_key = sanitize_filename(top_key) or "key_empty"

                for entry_index, entry in enumerate(entries):
                    # Each entry is a dictionary with keys like "ENAUG", "ENMAX", etc.
                    steps = entry.get('steps', [])
                    if not steps:
                        print(f"No 'steps' found in entry {entry_index} under key '{top_key}'. Skipping.")
                        continue

                    for step_index, step in enumerate(steps):
                        structure_dict = step.get('structure')
                        energy = step.get('energy')

                        if not structure_dict or energy is None:
                            print(f"Missing 'structure' or 'energy' in step {step_index} of entry {entry_index} under key '{top_key}'. Skipping.")
                            skipped += 1
                            continue

                        # Generate POSCAR filename consistent with makePOSCARs.py
                        poscar_filename = f"POSCAR_{sanitized_base_filename}_{sanitized_top_key}_entry{entry_index}_step{step_index}.vasp"

                        # Write to the id_prop.csv file
                        try:
                            writer.writerow([poscar_filename, energy])
                            #print(f"Written to id_prop.csv: {poscar_filename}, {energy}")
                        except Exception as e:
                            print(f"Error writing to id_prop.csv for {poscar_filename}: {e}")
                            skipped += 1
                            continue

        print(f"\nAll data has been processed. Number of entries skipped: {skipped}")

if __name__ == "__main__":
    main()
