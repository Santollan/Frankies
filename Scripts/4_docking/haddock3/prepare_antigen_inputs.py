from pymol import cmd
from random import sample
import pandas as pd
from pathlib import Path
import logging
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--input_pdb_path", help="The file path to the input PDB file.")
parser.add_argument("--output_pdb_path", help="The file path to save the output PDB file.")
parser.add_argument("--resn_offset", help="The offset to add to the residue numbers.", default=1000, type=int)
parser.add_argument("--percentage", help="The percentage of random surface residues to select.", default=0.25, type=float)

args = parser.parse_args()

input_pdb_path = args.input_pdb_path
output_pdb_path = args.output_pdb_path
resn_offset = args.resn_offset
percentage = args.percentage

def prepare_antigen_structure(file, output_file, resn_offset = 1000):
    """
    Prepare the antigen structure for docking.
    Places all the residues in chain B and renumbers them.
    """
    ## Read in file
    cmd.load(file)

    ## Put everything in chain B
    cmd.alter('all', "chain='B'")
    ## Renumber to start at desired residue number
    cmd.alter('chain B', f'resi=int(resi)+{resn_offset}')

    ## Save the PDB file
    cmd.save(output_file, selection='all', format='pdb')
    cmd.reinitialize('everything')


def find_random_surface_residues(file, percentage = 0.25):
    """
    Find a random subset of surface residues from a PDB file.
    """
    cmd.load(file)
    ## Finds atoms on the surface of a protein
    ## Logic from: https://pymolwiki.org/index.php/FindSurfaceResidues
    cutoff = 2.0
    tmpObj = cmd.get_unused_name("_tmp")

    cmd.create(tmpObj, "(all) and polymer", zoom=0)
    cmd.set("dot_solvent", 1, tmpObj)
    cmd.get_area(selection=tmpObj, load_b=1)
    cmd.remove(tmpObj + " and b < " + str(cutoff))
    cmd.select("exposed_atoms", "(all) in " + tmpObj)
    cmd.delete(tmpObj)

    ## Get a list of residue numbers and then subset it
    surface_residues = set()
    cmd.iterate('exposed_atoms', "surface_residues.add(resi)", space=locals())

    k = int(len(surface_residues) * percentage)

    surface_residues_sample = list(sample(surface_residues, k))
    surface_residues_sample = [int(x) for x in surface_residues_sample]
    surface_residues_sample.sort()

    ## Reintialize Everything
    cmd.reinitialize(what='everything')

    return surface_residues_sample

## Main Function
if __name__ == '__main__':
    ## Set up logging
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting antigen file preparation...")

    ## Prepare output directory (if it doesn't exist)
    logging.info(f"Preparing output directory: {Path(output_pdb_path).parent}")
    Path(output_pdb_path).parent.mkdir(parents=True, exist_ok=True)

    ## Prepare the antigen structure
    logging.info(f"Preparing antigen structure: {output_pdb_path}")
    try:
        prepare_antigen_structure(
            input_pdb_path,
            output_pdb_path,
            resn_offset=resn_offset)
    except Exception as e:
        logging.error(f"Error preparing antigen structure: {e}")

    ## Get a list of random surface residues
    logging.info(f"Finding random surface residues")
    try:
        surface_residues = find_random_surface_residues(
            output_pdb_path,
            percentage=percentage
            )
    except Exception as e:
        logging.error(f"Error finding random surface residues: {e}")

    ## Write list of surface residues to the output directory
    output_residues_file = Path(output_pdb_path).parent.joinpath('surface_residues.txt')
    logging.info(f"Writing surface residues to file: {output_residues_file}")
    try:
        with open(output_residues_file, 'w') as f:
            f.write(','.join(str(res) for res in surface_residues))
    except Exception as e:
        logging.error(f"Error writing surface residues to file: {e}")
