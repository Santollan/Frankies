
## Run antigen preparation
python ../prepare_antigen_inputs.py --input_pdb_path 2vir_chainC_antigen.pdb --output_pdb_path ./2vir_antigen_prepared.pdb --resn_offset 1000 --percentage 0.25

## Run antibody preparation
python ../prepare_antibody_inputs.py --input_pdb_path 2vir_chainsAB_antibody.pdb --output_pdb_path ./2vir_antibody_prepared.pdb --H_chain_id A --L_chain_id B --L_resn_offset 1000