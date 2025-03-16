import sys
sys.path.append('/workspace/evodiff')
from evodiff.pretrained import MSA_OA_DM_MAXSUB
from evodiff.generate_msa import generate_query_oadm_msa_simple
import re
import torch
import argparse
import os
import json
from abnumber import Chain

# Check if CUDA is available
print(torch.cuda.is_available())
torch.set_default_device('cpu')

# Argument parsing for the user inputs
parser = argparse.ArgumentParser()

# Add arguments
parser.add_argument("--sequence_count", help="The number of sequences in MSA subsample", type=int)
parser.add_argument("--max_sequence", help="maximum sequence length to subsample", type=int)
parser.add_argument("--path", help="The file path of the Chain", type=str)
parser.add_argument("--chain", help="The file name of the Chain", type=str)

args = parser.parse_args()

# Loading the Evodiff model
sequence_count = args.sequence_count
max_sequence = args.max_sequence
selection_type = 'MaxHamming'  # Or 'Random'; MSA subsampling scheme
output_data = {'generated_sequence': []}

checkpoint = MSA_OA_DM_MAXSUB()
model, collater, tokenizer, scheme = checkpoint

# Function to check if the sequence is compatible with abnumber
def check_with_abnumber(sequence):
    try:
        # Clean the sequence of any non-standard characters (like gaps or padding)
        cleaned_sequence = re.sub('[!-]', '', sequence)
        
        # Attempt to create a Chain object with abnumber
        chain = Chain(cleaned_sequence, scheme='Chothia')  # Use the Chothia scheme for antibody numbering
        # Check if the sequence is valid
        if not chain.is_valid():
            print("Invalid sequence for abnumber.")
            return False  # Sequence failed
        # Check if the sequence is an antibody
        if not chain.is_antibody():
            print("The sequence is not an antibody.")
            return False  # Sequence failed

        
        # Check if CDR3 region is found
        cdr3 = chain.cdr3_seq
        if cdr3:
            print(f"CDR3 Region: {cdr3}")
            return True  # Sequence passed
        else:
            print("CDR3 Region could not be identified.")
            return False  # Sequence failed
    except Exception as e:
        print(f"Error processing sequence with abnumber: {e}")
        return False  # Sequence failed

# Function to attempt generating a valid sequence multiple times
def attempt_sequence_generation(file_path, model, tokenizer, sequence_count, max_sequence, selection_type, max_attempts=10):
    successes = 0
    failures = 0
    attempt = 0
    
    # Output directory for saving generated sequences
    output_dir = '/workspace/evodiff/frankie/experiment/2_diffusion'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # Ensure output directory exists
    
    while attempt < max_attempts:
        print(f"Attempt {attempt + 1} of {max_attempts}")
        
        # Generate new sequence
        tokenized_sample, generated_sequence = generate_query_oadm_msa_simple(file_path, model, tokenizer, sequence_count, max_sequence, device='cpu', selection_type=selection_type)
        
        # Clean the sequence
        generated_seq = re.sub('[!-]', '', generated_sequence[0][0])  # Clean the generated sequence
        
        # Check if the generated sequence is compatible with abnumber
        if check_with_abnumber(generated_seq):
            successes += 1
            output_data['generated_sequence'].append(generated_sequence)
            # Save the generated sequence with sequential numbering
            output_file_path = os.path.join(output_dir, f"{args.chain}_generated_sequence_{successes}.json")
            with open(output_file_path, 'w') as json_file:
                json.dump({"generated_sequence": generated_sequence}, json_file, indent=4)
            print(f"Sequence {attempt + 1} succeeded and saved as {output_file_path}")
        else:
            failures += 1
            print(f"Sequence {attempt + 1} failed.")
        
        attempt += 1
    
    return successes, failures

# File path to the MSA (using the arguments from parser)
file_path = os.path.join(args.path, args.chain)

# Attempt generating a sequence up to 10 times
successes, failures = attempt_sequence_generation(file_path, model, tokenizer, sequence_count, max_sequence, selection_type)

# Output the number of successes and failures
print(f"Total successes: {successes}")
print(f"Total failures: {failures}")

# If no valid sequences were generated, report that
if successes == 0:
    print("No valid sequences were generated after 10 attempts.")
