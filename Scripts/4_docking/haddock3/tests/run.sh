## Run antigen preparation
python ../prepare_antigen_inputs.py --input_pdb_path 2vir_chainC_antigen.pdb --output_pdb_path ./2vir_antigen_prepared.pdb --resn_offset 1000 --percentage 0.25

## Run antibody preparation
python ../prepare_antibody_inputs.py --input_pdb_path 2vir_chainsAB_antibody.pdb --output_pdb_path ./2vir_antibody_prepared.pdb --H_chain_id A --L_chain_id B --L_resn_offset 1000


## Prepare experiment
python ../create_haddock_experiment.py --experiment_path ./ --antibody_pdb_path 2vir_chainsAB_antibody.pdb --antigen_pdb_path 2vir_antigen_prepared.pdb --active_antibody_path cdr_residues.txt --active_antigen surface_residues.txt --config_template_path ../antibody_antigen_template_custom.cfg


## Run HADDOCK
haddock3 config.cfg