import json
import argparse
import os


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare input files for AlphaFold3.")

    # Adding arguments
    parser.add_argument(
        "--hchain_file",
        type=str,
        required=True,
        help="Path to the H-chain aligned JSON file."
    )

    parser.add_argument(
        "--lchain_file",
        type=str,
        required=True,
        help="Path to the L-chain aligned JSON file."
    )

    parser.add_argument(
        "--output_file",
        type=str,
        required=True,
        help="Path to save the final AlphaFold3 input JSON."
    )

    return parser.parse_args()

def generate_alphafold_json(hchain_file, lchain_file, output_file):
    # check if the output directory exists
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load the Hchain and Lchain JSON files
    with open(hchain_file, 'r') as f:
        hchain_data = json.load(f)
    
    with open(lchain_file, 'r') as f:
        lchain_data = json.load(f)
    
    # Extract the clean generated sequences
    hchain_sequence = hchain_data['cleaned_sequence'][0][0]
    lchain_sequence = lchain_data['cleaned_sequence'][0][0]

    # Create the structure for AlphaFold3 JSON
    alphafold_data = {
        "name": "Antibody",
        "modelSeeds": [1234],
        "sequences": [
            {
                "protein": {
                    "id": "H",
                    "sequence": hchain_sequence.strip()
                }
            },
            {
                "protein": {
                    "id": "L",
                    "sequence": lchain_sequence.strip()
                }
            }
        ],
        "dialect": "alphafold3",
        "version": 1
    }
    
    # Save the generated data into a new JSON file
    with open(output_file, 'w') as f:
        json.dump(alphafold_data, f, indent=4)
    
    print(f" Generated AlphaFold JSON saved to: {output_file}")

if __name__ == "__main__":
    args = parse_args()
    
    # Print input paths for debugging
    print(f"H-chain file: {args.hchain_file}")
    print(f"L-chain file: {args.lchain_file}")
    print(f"Output file: {args.output_file}")

    # Generate the AlphaFold JSON
    generate_alphafold_json(args.hchain_file, args.lchain_file, args.output_file)

