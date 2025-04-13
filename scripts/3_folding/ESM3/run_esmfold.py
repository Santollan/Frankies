'''
Script to fold a protein sequence using ESMFold from the ESM library.
This script takes a protein sequence as input and outputs the predicted 3D structure in PDB format.
'''

import os
import logging
import json
# from esm.models.esm3 import ESM3
# from esm.sdk.api import (
#     ESMProtein,
#     GenerationConfig,
# )
from esm.sdk import client
from esm.sdk.api import ESMProtein, GenerationConfig
from esm.utils.structure.protein_chain import ProteinChain
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--input_h_json", help="The JSON file containing the H chain sequence", required=True)
parser.add_argument("--input_l_json", help="The JSON file containing the L chain sequence", required=True)
parser.add_argument("--model", help="The ESM multimer model to use", default="esm3-medium-multimer-2024-09")
parser.add_argument("--token", help="The ESM Forge token", default="")
# parser.add_argument("--gpus", help="The GPUs to use", default="all")
parser.add_argument("--output_pdb", help="The output PDB file to write", required=True)

args = parser.parse_args()

input_h_json = args.input_h_json
input_l_json = args.input_l_json
model_name = args.model
token = args.token
# gpus = args.gpus
output_pdb = args.output_pdb


def fix_multichain_pdb_str(pdb_str: str, chain_a_end_index: int) -> str:
    """Returns a fixed pdb string where all chains get unique identifiers.
    At the moment there is a bug where all the chains are written out as
    "Chain A". This function adjusts the second chain to have a unique chain
    identifier.
    Adapted from: https://colab.research.google.com/gist/thomas-a-neil/720683f97de624bc6822bf6e9629e298/forward_fold_multimer_dec_2024.ipynb#scrollTo=HDPnd-5xnAo2
    By Neil Thomas
    """
    fixed_lines = []
    for line in pdb_str.splitlines():
        if line.startswith("ATOM") or line.startswith("HETATM"):
            residue = line[17:20] # Residue name (4th column)
            chain = line[21]  # Chain identifier (5th column)
            residue_index = int(line[22:26].strip())  # Residue index (6th column)
            ## Replace the chain identifier with "H" or "L" depending on the split
            if residue_index > chain_a_end_index:
                # Replace the chain with "L"
                line = line[:21] + "L" + line[22:]
            else:
                line = line[:21] + "H" + line[22:]
            ## If residue is "UNK", remove the line
            if residue == "UNK":
                line = ""
        fixed_lines.append(line)
    return "\n".join(fixed_lines)

def fold_sequence(sequence:str, model_name:str, token:str) -> str:
    ## Load the ESM model
    model = client(model=model_name, url="https://forge.evolutionaryscale.ai", token=token)
    ## Prepare the sequence
    sequence = sequence.replace(" ", "").replace("\n", "")
    ## Generate the structure
    structure_prediction = model.generate(
        ESMProtein(sequence=sequence),
        GenerationConfig(
            track="structure", num_steps=len(sequence) // 4, temperature=0
        ),
    )
    ## Fix the PDB string to have L/H chain identifiers and remove "UNK" residues
    CHAIN_A_END_INDEX = structure_prediction.sequence.index("|")
    pdb_str = fix_multichain_pdb_str(structure_prediction.to_pdb_string(), CHAIN_A_END_INDEX)
    return pdb_str


## Main Function
if __name__ == '__main__':
    ## Set up logging
    logging.basicConfig(level=logging.INFO)
    logging.info("Folding with ESM3...")

    ## Read the input JSON file
    with open(input_h_json, "r") as f:
       h_json_data = json.load(f)
    with open(input_l_json, "r") as f:
       l_json_data = json.load(f)
    sequence = f'{h_json_data["cleaned_sequence"]}|{l_json_data["cleaned_sequence"]}'

    logging.info(f"Folding sequence: {sequence}.")

    try:
        structure = fold_sequence(sequence, model_name, token)
        logging.info("Folding completed successfully.")
    except Exception as e:
        logging.error(f"Error in folding: {e}")

    ## Save the structure to a PDB file
    if not os.path.exists(os.path.dirname(output_pdb)):
        os.makedirs(os.path.dirname(output_pdb))

    with open(output_pdb, "w") as f:
        f.write(structure)
    logging.info(f"Folded structure saved to {output_pdb}.")