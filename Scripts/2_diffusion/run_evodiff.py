import sys
sys.path.append('/workspace/evodiff')
from evodiff.pretrained import MSA_OA_DM_MAXSUB
from evodiff.generate_msa import generate_query_oadm_msa_simple
import re
import torch
import argparse
print(torch.cuda.is_available())
torch.set_default_device('cpu') #'cuda:0'


parser = argparse.ArgumentParser()

parser.add_argument("--sequence_count", help="The number of sequences in MSA subsample")
parser.add_argument("--max_sequence", help="maximum sequence length to subsample")
parser.add_argument("--chain", help="The file location of the Chain")
 
args = parser.parse_args()

# Debugging: Check if 'args.chain' is being passed correctly
print(f"Chain file path: {args.chain}")

sequence_count = int(args.sequence_count)
max_sequence = int(args.max_sequence)
file_path = args.chain

checkpoint = MSA_OA_DM_MAXSUB()
model, collater, tokenizer, scheme = checkpoint

#path_to_msa = file_path
path_to_msa = args.chain #'/workspace/evodiff/frankie/evodiff/tests/PD1_Hchains_aligned.a3m'  # Replace with your file path
n_sequences=sequence_count # number of sequences in MSA to subsample
seq_length=max_sequence # maximum sequence length to subsample
selection_type='random' # or 'MaxHamming'; MSA subsampling scheme

print(f"Path to MSA: {path_to_msa}")  # Debugging line


tokenized_sample, generated_sequence  = generate_query_oadm_msa_simple(path_to_msa, model, tokenizer, n_sequences, seq_length, device='cpu',
                                                                        selection_type=selection_type)

print("New H chain sequence (no gaps, pad tokens)", re.sub('[!-]', '', generated_sequence[0][0],))