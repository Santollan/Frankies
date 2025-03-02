import sys
sys.path.append('/workspace/evodiff')
from evodiff.pretrained import MSA_OA_DM_MAXSUB
from evodiff.generate_msa import generate_query_oadm_msa_simple
import re
import torch
import argparse
import os
import json
print(torch.cuda.is_available())
torch.set_default_device('cpu') #'cuda:0'


parser = argparse.ArgumentParser()

parser.add_argument("--sequence_count", help="The number of sequences in MSA subsample")
parser.add_argument("--max_sequence", help="maximum sequence length to subsample")
parser.add_argument("--path", help="The file path of the Chain")
parser.add_argument("--chain", help="The file name of the Chain")
 
args = parser.parse_args()


# Debugging: Check if 'args.chain' is being passed correctly
print(f"Chain file path: {os.path.join(args.path, args.chain)}")

sequence_count = int(args.sequence_count)
max_sequence = int(args.max_sequence)
file_path = os.path.join(args.path, args.chain)

checkpoint = MSA_OA_DM_MAXSUB()
model, collater, tokenizer, scheme = checkpoint

#path_to_msa = file_path
path_to_msa = os.path.join(args.path, args.chain) #'/workspace/evodiff/frankie/evodiff/tests/PD1_Hchains_aligned.a3m'  # Replace with your file path
n_sequences=sequence_count # number of sequences in MSA to subsample
seq_length=max_sequence # maximum sequence length to subsample
selection_type='random' # or 'MaxHamming'; MSA subsampling scheme

print(f"Path to MSA: {path_to_msa}")  # Debugging line


tokenized_sample, generated_sequence  = generate_query_oadm_msa_simple(path_to_msa, model, tokenizer, n_sequences, seq_length, device='cpu',
                                                                        selection_type=selection_type)

print(f"New {args.chain} chain sequence (no gaps, pad tokens)", re.sub('[!-]', '', generated_sequence[0][0],))

# Assuming 'tokenized_sample' or 'generated_sequence' is a tensor
tokenized_sample = tokenized_sample.tolist()  # Convert Tensor to list
generated_sequence = generated_sequence  # Convert each sequence to list if it's a tensor

# Prepare the data to be saved to JSON
output_data = {
    'generated_sequence': generated_sequence,
}

# Save the output data to a .json file
output_file_path = f'/workspace/evodiff/frankie/experiment/{args.chain}.json'  # Corrected to use f-string
with open(output_file_path, 'w') as json_file:
    json.dump(output_data, json_file, indent=4)

print(f"Output saved to {output_file_path}")
 