import sys
import re
import torch
import argparse
import os
import json
from pathlib import Path

# Add evodiff to path
sys.path.append('/workspace/evodiff')
from evodiff.pretrained import msa_d3pm_blosum_maxsub
from evodiff.generate_msa import generate_query_oadm_msa_simple

# Check CUDA availability
cuda_available = torch.cuda.is_available()
print(f"CUDA available: {cuda_available}")

# Set up argument parser
parser = argparse.ArgumentParser(description='Generate protein sequences using EvoDiff')
parser.add_argument("--sequence_count", type=int, required=True, help="The number of sequences in MSA subsample")
parser.add_argument("--max_sequence", type=int, required=True, help="Maximum sequence length to subsample")
parser.add_argument("--path", required=True, help="The directory path containing the MSA file")
parser.add_argument("--chain", required=True, help="The filename of the MSA file")
parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="Device to run inference on (cpu or cuda)")
parser.add_argument("--output_dir", default="/workspace/evodiff/frankie/experiment/2_diffusion/", 
                    help="Directory to save output JSON")
args = parser.parse_args()

# Use the specified device or fallback to CPU if CUDA requested but unavailable
device = "cuda" if args.device == "cuda" and cuda_available else "cpu"
print(f"Using device: {device}")

# Set the torch default device
if device == "cuda":
    torch.set_default_device('cuda:0')
else:
    torch.set_default_device('cpu')

# Construct the full path to the MSA file
msa_path = os.path.join(args.path, args.chain)
print(f"Loading MSA from: {msa_path}")

# Check if the MSA file exists
if not os.path.exists(msa_path):
    print(f"Error: MSA file not found at {msa_path}")
    sys.exit(1)

# Load the EvoDiff model
print(f"Loading the EvoDiff model for {args.chain}")
try:
    checkpoint = msa_d3pm_blosum_maxsub()
    model, collater, tokenizer, scheme = checkpoint
except Exception as e:
    print(f"Error loading model: {e}")
    sys.exit(1)

# Standard amino acids for filtering
STANDARD_AA = set("ACDEFGHIKLMNPQRSTVWY")
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

def clean_sequence(seq):
    """Clean the sequence by removing padding tokens and mapping non-standard amino acids."""
    # Remove padding tokens and any non-amino acid characters
    seq = re.sub(r'[!-]', '', seq)
    
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

# Generate sequences
try:
    print(f"Generating sequences with {args.sequence_count} count and max length {args.max_sequence}")
    tokenized_sample, generated_sequence = generate_query_oadm_msa_simple(
        msa_path, model, tokenizer, 
        n_sequences=args.sequence_count, 
        seq_length=args.max_sequence, 
        device=device,
        selection_type='MaxHamming'  # or 'random'
    )
except Exception as e:
    print(f"Error during sequence generation: {e}")
    sys.exit(1)

# Clean generated sequences
clean_sequences = []
for seq_batch in generated_sequence:
    batch_clean = []
    for seq in seq_batch:
        cleaned = clean_sequence(seq)
        batch_clean.append(cleaned)
    clean_sequences.append(batch_clean)

# Print the first cleaned sequence
if clean_sequences and clean_sequences[0]:
    print(f"New {args.chain} chain sequence (cleaned): {clean_sequences[0][0]}")

# Prepare output data
output_data = {
    'generated_sequence': generated_sequence,
    'cleaned_sequence': clean_sequences
}

# Create output directory if it doesn't exist
Path(args.output_dir).mkdir(parents=True, exist_ok=True)

# Save the output data to a JSON file
output_file_path = os.path.join(args.output_dir, f"{args.chain}.json")
with open(output_file_path, 'w') as json_file:
    json.dump(output_data, json_file, indent=2)  # Increased indentation for better readability

print(f"Output saved to {output_file_path}")