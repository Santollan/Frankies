
from pathlib import Path
import logging
import configparser
import argparse
import shutil

parser = argparse.ArgumentParser()

parser.add_argument("--experiment_path", help="Path to the experiment folder.")
parser.add_argument("--antibody_pdb_path", help="Path to the antibody PDB file.")
parser.add_argument("--antigen_pdb_path", help="Path to the antigen PDB file.")
parser.add_argument("--active_antibody_path", help="Path to comma-separated list of active residues in the antibody PDB file.")
parser.add_argument("--active_antigen_path", help="Path to comma-separated list of active residues in the antigen PDB file.")
parser.add_argument("--config_template_path", help="Path to template config file.")

args = parser.parse_args()

experiment_path = args.experiment_path
antibody_pdb_path = args.antibody_pdb_path
antigen_pdb_path = args.antigen_pdb_path
active_antibody_path = args.active_antibody_path
active_antigen_path = args.active_antigen_path
config_template_path = args.config_template_path


## Copy the antibody and antigen PDB files to the experiment directory
logging.info(f"Copying antibody PDB file to experiment directory: {antibody_pdb_path} -> {experiment_path}/antibody.pdb")
def copy_experiment_files(antibody_pdb_path, antigen_pdb_path, experiment_path):
    shutil.copy(antibody_pdb_path, f"{experiment_path}/antibody.pdb")
    shutil.copy(antigen_pdb_path, f"{experiment_path}/antigen.pdb")

## Define functions for creating ambiguous AIR files
def write_ambig_air_file(active1, passive1, active2, passive2, segid1='A', segid2='B', output_file="ambig.tbl"):
    with open(output_file, "w") as output_file:
        ## Convert residues to integers
        active1 = [int(x) for x in active1]
        passive1 = [int(x) for x in passive1]
        active2 = [int(x) for x in active2]
        passive2 = [int(x) for x in passive2]
        all1 = active1 + passive1
        all2 = active2 + passive2

        ## Write lines from the active1 list
        for resi1 in active1:
            output_file.write('assign (resi {:d} and segid {:s})'.format(resi1, segid1) + '\n')
            output_file.write('(\n')
            c = 0
            for resi2 in all2:
                output_file.write('       (resi {:d} and segid {:s})'.format(resi2, segid2) + '\n')
                c += 1
                if c != len(all2):
                    output_file.write('        or\n')
            output_file.write(') 2.0 2.0 0.0\n\n')

        ## Write lines from the active2 list
        for resi2 in active2:
            output_file.write('assign (resi {:d} and segid {:s})'.format(resi2, segid2) + '\n')
            output_file.write('(\n')
            c = 0
            for resi1 in all1:
                output_file.write('       (resi {:d} and segid {:s})'.format(resi1, segid1) + '\n')
                c += 1
                if c != len(all1):
                    output_file.write('        or\n')
            output_file.write(') 2.0 2.0 0.0\n\n')

    ## File will be closed automatically when exiting the 'with' block

def create_config(
      antibody_pdb = 'antibody.pdb',
      antigen_pdb = 'antibody.pdb',
      # reference_pdb = 'refD.pdb',
      ambig_fname = "ambig.tbl",
      # unambig_fname = "unambig.tbl",
      template_file = 'antibody_antigen_template_custom.cfg',
      output_file = 'config.cfg'
                  ):
    
    config = configparser.ConfigParser()

    ## Read the configuration file
    config.read(template_file)

    ## Update the configuration
    config['main'] = {'run_dir': '"./output"',
                      'mode': '"local"',
                      'ncores': 36,
                     #  'concat':  5,
                     #  'queue_limit': 100,
                      'molecules': [
                            antibody_pdb,
                            antigen_pdb
                            ]}
 
    ## Write the configuration to a file
    with open(output_file, 'w') as configfile:
        config.write(configfile)

    ## Replace specific lines in config file (HACKY FIX)
    with open(output_file, 'r') as configfile:
      cfgdata = configfile.read()
    cfgdata = cfgdata.replace('[main]', '## Antibody-Antigen Docking with HADDOCK3') \
                    .replace('[clustfcc_0]', '[clustfcc]') \
                    .replace('[clustfcc_1]', '[clustfcc]') \
                    .replace('[clustfcc_2]', '[clustfcc]') \
                    .replace('[seletopclusts_0]', '[seletopclusts]') \
                    .replace('[seletopclusts_1]', '[seletopclusts]')
                                                                                                         
    ## Write the file out again
    with open(output_file, 'w') as configfile:
      configfile.write(cfgdata)


## Main Function
if __name__ == '__main__':
    ## Set up logging
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting experiment generation...")

    ## Prepare experiment directory (if it doesn't exist)
    logging.info(f"Preparing experiment directory: {Path(experiment_path).parent}")
    Path(experiment_path).parent.mkdir(parents=True, exist_ok=True)

    ## Copy the antibody and antigen PDB files to the experiment directory
    logging.info(f"Copying antibody and antigen PDB files to experiment directory...")
    try:
        copy_experiment_files(antibody_pdb_path, antigen_pdb_path, experiment_path)
    except Exception as e:
        logging.error(f"Error copying PDB files to experiment directory: {e}")

    ## Prepare the AIR file
    logging.info(f"Preparing AIR file...")
    try:
        with open(active_antibody_path, 'r') as file:
            active_antibody = file.readline().split(',')

        with open(active_antigen_path, 'r') as file:
            active_antigen = file.readline().split(',')

        active1 = active_antibody
        passive1 = []
        active2 = active_antigen
        passive2 = []
        write_ambig_air_file(active1, passive1, active2, passive2, segid1='A', segid2='B', output_file=f"{experiment_path}/ambig.tbl")
    except Exception as e:
        logging.error(f"Error preparing AIR file: {e}")

    ## Get a list of random surface residues
    logging.info(f"Preparing config file...")
    try:
        create_config(
          antibody_pdb = f"{experiment_path}/antibody.pdb",
          antigen_pdb = f"{experiment_path}/antibody.pdb",
          ambig_fname = f"{experiment_path}ambig.tbl",
          template_file = config_template_path,
          output_file = f"{experiment_path}/config.cfg"
          )
    except Exception as e:
        logging.error(f"Preparing config file: {e}")