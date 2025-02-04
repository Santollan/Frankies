from pymol import cmd
from random import sample
# import pandas as pd
import biopandas.pdb as pd
from biopandas.pdb import PandasPdb
import numpy as np
from abnumber import Chain

import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--input_pdb_path", help="The file path to the input PDB file.")
parser.add_argument("--output_pdb_path", help="The file path to save the output PDB file.")
parser.add_argument("--H_chain_id", help="The chain ID of the heavy chain in the PDB file.", default='A', type=str)
parser.add_argument("--L_chain_id", help="The chain ID of the light chain in the PDB file.", default='B', type=str)
parser.add_argument("--L_resn_offset", help="The offset to add to the L chain residue numbers.", default=1000, type=int)

args = parser.parse_args()

input_pdb_path = args.input_pdb_path
output_pdb_path = args.output_pdb_path
H_chain_id = args.H_chain_id
L_chain_id = args.L_chain_id
L_resn_offset = args.L_resn_offset


##########
## Residue Selection Functions
##########

def get_cdr_resn(protein_atoms, scheme):
    ## Define lookup dictionary for amino acid symbols
    resns = {'CYS': 'C', 'ASP': 'D', 'SER': 'S', 'GLN': 'Q', 'LYS': 'K',
             'ILE': 'I', 'PRO': 'P', 'THR': 'T', 'PHE': 'F', 'ASN': 'N', 
             'GLY': 'G', 'HIS': 'H', 'LEU': 'L', 'ARG': 'R', 'TRP': 'W', 
             'ALA': 'A', 'VAL': 'V', 'GLU': 'E', 'TYR': 'Y', 'MET': 'M'}
             
    ## Get array of residees (in 3 letter format)
    residues = protein_atoms.groupby('residue_number')['residue_name'].apply(set).apply(''.join)

    ## Remember sequence starting posistion (as it may not be 1)
    seq_start_pos = min(residues.keys())
    # seq_end_pos = max(residues.keys())

    ## Convert 3 letter amino acids to 1 letter and make string
    seq = ''.join([resns[a] for a in list(residues)])

    ## Parse sequence to detect CDR loops
    chain = Chain(seq, scheme=scheme)

    ## Get CDR loops' residues numbers
    cdr1_seq = chain.cdr1_seq
    cdr1_start_pos = seq.find(cdr1_seq) + seq_start_pos
    cdr1_end_pos = cdr1_start_pos + len(cdr1_seq) - 1
    cdr1_resn = [str(n) for n in range(cdr1_start_pos, cdr1_end_pos+1)]

    cdr2_seq = chain.cdr2_seq
    cdr2_start_pos = seq.find(cdr2_seq) + seq_start_pos
    cdr2_end_pos = cdr2_start_pos + len(cdr2_seq) - 1
    cdr2_resn = [str(n) for n in range(cdr2_start_pos, cdr2_end_pos+1)]

    cdr3_seq = chain.cdr3_seq
    cdr3_start_pos = seq.find(cdr3_seq) + seq_start_pos
    cdr3_end_pos = cdr3_start_pos + len(cdr3_seq) - 1
    cdr3_resn = [str(n) for n in range(cdr3_start_pos, cdr3_end_pos+1)]

    return cdr1_resn + cdr2_resn + cdr3_resn

def find_cdr_residues(file, L_resn_offset = 1000):
    ## Read in the PDB file
    pdb = PandasPdb().read_pdb(file)

    ## Get PDB atoms
    pdb_atoms = pdb.df['ATOM']

    ## Filter to Fab H and L chains
    atoms_fab_H = pdb_atoms[pdb_atoms['chain_id'] == 'A'][pdb_atoms['residue_number'] < L_resn_offset]
    atoms_fab_L = pdb_atoms[pdb_atoms['chain_id'] == 'A'][pdb_atoms['residue_number'] >= L_resn_offset]

    scheme = "chothia" # or "imgt"

    H_cdr_residue_numbers = get_cdr_resn(atoms_fab_H, scheme = scheme)
    L_cdr_residue_numbers = get_cdr_resn(atoms_fab_L, scheme = scheme)

    return H_cdr_residue_numbers + L_cdr_residue_numbers

##########
## Structure Preparation Functions
##########

def prepare_antibody_structure(file, output_file, H_chain_id="A", L_chain_id="B", L_resn_offset = 1000):
    ## Read in file
    cmd.load(file)

    ## Change chains to H and L (if necessary)
    cmd.alter(f'chain {H_chain_id}', "chain='H'")
    cmd.alter(f'chain {L_chain_id}', "chain='L'")

    ## Renumber L chain to start at an offset
    cmd.alter('chain L', f'resi=int(resi)+{L_resn_offset}')
    
    ## Put everything in chain A
    cmd.alter('all', "chain='A'")
    
    ## Save the PDB file
    cmd.save(output_file, selection='all', format='pdb')
    cmd.reinitialize('everything')



## Main Function
if __name__ == '__main__':
    ## Set up logging
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting antibody file preparation...")

    ## Prepare output directory (if it doesn't exist)
    logging.info(f"Preparing output directory: {Path(output_pdb_path).parent}")
    Path(output_pdb_path).parent.mkdir(parents=True, exist_ok=True)

    ## Prepare the antibody structure
    logging.info(f"Preparing antibody structure: {output_pdb_path}")
    try:
        prepare_antibody_structure(
            input_pdb_path,
            output_pdb_path,
            H_chain_id=H_chain_id,
            L_chain_id=L_chain_id,
            L_resn_offset=L_resn_offset)
    except Exception as e:
        logging.error(f"Error preparing antibody structure: {e}")

    ## Get a list of random surface residues
    logging.info(f"Finding random surface residues")
    try:
        surface_residues = find_cdr_residues(
            output_pdb_path,
            L_resn_offset=L_resn_offset
            )
    except Exception as e:
        logging.error(f"Error finding CDR residues: {e}")

    ## Write list of surface residues to the output directory
    output_residues_file = Path(output_pdb_path).parent.joinpath('cdr_residues.txt')
    logging.info(f"Writing CDR residues to file: {output_residues_file}")
    try:
        with open(output_residues_file, 'w') as f:
            f.write(','.join(str(res) for res in surface_residues))
    except Exception as e:
        logging.error(f"Error writing CDR residues to file: {e}")