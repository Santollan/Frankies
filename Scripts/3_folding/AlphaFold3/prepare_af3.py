import json
import argparse
import os
import re

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

def clean_sequence(seq):
    """Clean the sequence by removing padding tokens and mapping non-standard amino acids."""
    # Remove padding tokens and any non-amino acid characters
    seq = re.sub(r'[!-]', '', seq)
    
    # Standard amino acids for filtering
    STANDARD_AA = set("ACDEFGHIKLMNPQRSTVWY")
    
    # Non-standard mapping dictionary
    NON_STANDARD_MAPPING = {
        'B': 'D',  # Aspartic acid or Asparagine -> Aspartic acid
        'Z': 'E',  # Glutamic acid or Glutamine -> Glutamic acid
        'X': 'A',  # Unknown -> Alanine (arbitrary choice)
        'U': 'C',  # Selenocysteine -> Cysteine
        'O': 'K',  # Pyrrolysine -> Lysine
        'J': 'L',  # Not standard -> Leucine (closest biochemical property)
        '*': '',   # Stop codon -> Remove
        '~': '',   # Non-standard -> Remove
        '.': '',   # Sometimes used as a gap -> Remove
    }
    
    # Map non-standard amino acids to standard ones
    cleaned_seq = ''
    for aa in seq:
        if aa in STANDARD_AA:
            cleaned_seq += aa
        elif aa in NON_STANDARD_MAPPING:
            cleaned_seq += NON_STANDARD_MAPPING[aa]
        else:
            # Log any uncovered non-standard amino acids and default to Alanine
            print(f"Warning: Encountered unknown amino acid code '{aa}', replacing with 'A'")
            cleaned_seq += 'A'
    
    return cleaned_seq

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
    
    # Extract the generated sequences
    hchain_sequence = hchain_data['generated_sequence'][0][0]
    lchain_sequence = lchain_data['generated_sequence'][0][0]
    
    # Clean sequences
    hchain_sequence_cleaned = clean_sequence(hchain_sequence)
    lchain_sequence_cleaned = clean_sequence(lchain_sequence)
    
    # Log the cleaning results
    print(f"H-chain original length: {len(hchain_sequence)}, cleaned length: {len(hchain_sequence_cleaned)}")
    print(f"L-chain original length: {len(lchain_sequence)}, cleaned length: {len(lchain_sequence_cleaned)}")
    
    # Create the structure for AlphaFold3 JSON
    alphafold_data = {
        "name": "Antibody",
        "modelSeeds": [1234],
        "sequences": [
            {
                "protein": {
                    "id": "H",
                    "sequence": hchain_sequence_cleaned
                }
            },
            {
                "protein": {
                    "id": "L",
                    "sequence": lchain_sequence_cleaned
                }
            }
        ],
        "dialect": "alphafold3",
        "version": 1
    }
    
    # Save the generated data into a new JSON file
    with open(output_file, 'w') as f:
        json.dump(alphafold_data, f, indent=4)
    
    print(f"Generated AlphaFold JSON saved to: {output_file}")
    
    # Also save the cleaned sequences back to the original files (optional)
    hchain_data['cleaned_sequence'] = [[hchain_sequence_cleaned]]
    lchain_data['cleaned_sequence'] = [[lchain_sequence_cleaned]]
    
    with open(hchain_file, 'w') as f:
        json.dump(hchain_data, f, indent=4)
    with open(lchain_file, 'w') as f:
        json.dump(lchain_data, f, indent=4)
    
    print(f"Updated original files with cleaned sequences")

if __name__ == "__main__":
    args = parse_args()
    # Print input paths for debugging
    print(f"H-chain file: {args.hchain_file}")
    print(f"L-chain file: {args.lchain_file}")
    print(f"Output file: {args.output_file}")
    # Generate the AlphaFold JSON
    generate_alphafold_json(args.hchain_file, args.lchain_file, args.output_file)