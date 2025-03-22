import os
configfile: "config.yaml"

rule all:
    input: "Scripts/6_postprocess/helloworld.txt"

rule initialize:
    params:
        experiment_dir = config["main"]["experiment_dir"],
    output:
       "{params.experiment_dir}/frankies.log"
    run: 
        shell("mkdir -p {params.experiment_dir}"),
        shell("echo \"Frankies pipeline started at: $(date)\" > {output}"),
        shell("docker info || echo 'Docker is not running. Please start Docker Desktop.'")

# rule frank_preprocess:
#     output: "Scripts/1_preprocess/helloworld.txt"
#     shell: "echo hello_frankie > Scripts/1_preprocess/helloworld.txt"

rule run_evodiff:
    params:
        experiment_dir=config["main"]["experiment_dir"],
        exeriment_name=config["main"]["experiment_name"],
        container_engine=config["main"]["container_engine"],
        H_chain=config["diffusion"]["evodiff"]["H_chain"],
        L_chain=config["diffusion"]["evodiff"]["L_chain"],
        H_chain_file=config["main"]["experiment_dir"] + "/01_inputs/" + config["diffusion"]["evodiff"]["H_chain"],  # path to Hchain file
        L_chain_file=config["main"]["experiment_dir"] + "/01_inputs/" + config["diffusion"]["evodiff"]["L_chain"],  # path to Lchain file  
        H_chain_json=config["main"]["experiment_dir"]+"/2_diffusion/"+config["diffusion"]["evodiff"]["H_chain"]+".json",  # path to Hchain file
        L_chain_json=config["main"]["experiment_dir"]+"/2_diffusion/"+config["diffusion"]["evodiff"]["L_chain"]+".json",  # path to Lchain file
        prep_output_file=config["main"]["experiment_dir"]+"/3_folding/af_input/"+config["folding"]["alphafold3"]["prep_output_file_name"]
    input:
        Hchain_file=config["main"]["experiment_dir"] + "/01_inputs/" + config["diffusion"]["evodiff"]["H_chain"],  # path to Hchain file
    output:
        config["main"]["experiment_dir"]+"/3_folding/af_input/"+config["folding"]["alphafold3"]["prep_output_file_name"], # path to output file

    shell:
        """
sudo docker run --gpus all --ipc=host --userns=host --ulimit memlock=-1 --ulimit stack=67108864 \
  -v {params.experiment_dir}:/workspace/evodiff/frankie/experiment:rw \
  -v ./Scripts/2_diffusion:/workspace/evodiff/frankie:rw \
  -it --rm cford38/evodiff:v1.1.0 /bin/bash -c \
  "conda install -c bioconda abnumber -y && \
  python3 /workspace/evodiff/frankie/prepare_evodiff.py --path /workspace/evodiff/frankie/experiment/01_inputs/ --chain {params.H_chain} && \
   python3 /workspace/evodiff/frankie/prepare_evodiff.py --path /workspace/evodiff/frankie/experiment/01_inputs/ --chain {params.L_chain}" && \
    python3 Scripts/3_folding/AlphaFold3/prepare_af3.py \
        --hchain_file {params.H_chain_json} \
        --lchain_file {params.L_chain_json} \
        --output_file {params.prep_output_file} 
   """



# rule run_igFold:
#     params:
#         experiment_dir=config["main"]["experiment_dir"],
#     input:
#         Hchain_file=config["main"]["experiment_dir"] + "/2_diffusion/" + config["diffusion"]["evodiff"]["H_chain"],  # path to Hchain file
#         Lchain_file=config["main"]["experiment_dir"] + "/2_diffusion/" + config["diffusion"]["evodiff"]["L_chain"]   # path to Lchain file
#     output:
#         "{params.experiment_dir}/3_folding/lgFold/my_antibody.pdb"
#     shell:
#         """
#         python3 ./Scripts/3_folding/lgFold/run_lgFold.py --input {input.Hchain_file} --output experiments/test/3_folding/lgFold/

#         """


#     input: 
#         # prepare_evodiff= os.path.join(os.getcwd(), "Scripts/2_diffusion/prepare_evodiff.py"),
#         # Chain=config["Evo"]["H_Chain"]
#     output: "Scripts/3_diffusion/helloworld.txt"
#     shell: "conda activate evodiff && python3 {input.prepare_evodiff} --chain {input.Chain}" #this will need to trigger the prepare_evodiff.py

# rule antigen_folding:
#     input:
#         seq=config["main"]["antigen"]["sequence"]
#     output:
#         structure=config["main"]["antigen"]["structure"] # Dynamic output path

#     shell: """
#         run_af3.sh --fasta_path {input.seq} --output_path {output.structure}
#     """

rule frank_folding:
    params:
        experiment_dir=config["main"]["experiment_dir"],
        af3_input_dir=config["main"]["experiment_dir"]+"/3_folding/af_input",
        output_pdb=config["main"]["experiment_dir"]+"/4_docking/antibody.pdb"
    input:
        config["main"]["experiment_dir"]+"/3_folding/af_input/"+config["folding"]["alphafold3"]["prep_output_file_name"], # path to AlphaFold3 input file
        # config["main"]["experiment_dir"]+"/2_diffusion/"+config["diffusion"]["evodiff"]["H_chain"]+".json",  # path to Hchain file
        # config["main"]["experiment_dir"]+"/2_diffusion/"+config["diffusion"]["evodiff"]["L_chain"]+".json", 
        # seq=os.path.join(os.getcwd(), "data/processed/3_diffusion/af_input"),
        output_model=config["main"]["experiment_dir"]+"/3_folding/af_output",
        weights_dir=config["folding"]["alphafold3"]["weights_dir"],
        databases_dir=config["folding"]["alphafold3"]["databases_dir"],
 
    output:
        config["main"]["experiment_dir"]+"/4_docking/antibody.pdb" # path to output file
    shell: """
        docker run --rm -it \
            --volume {params.af3_input_dir}:/root/af_input \
            --volume {input.output_model}:/root/af_output \
            --volume {input.weights_dir}:/root/models \
            --volume {input.databases_dir}:/root/public_databases \
            --gpus all \
            alphafold3 \
            python run_alphafold.py \
            --json_path=/root/af_input/alphafold_input.json \
            --model_dir=/root/models \
            --db_dir=/root/public_databases \
            --db_dir=/root/public_databases_fallback \
            --output_dir=/root/af_output && \
        python3 ./Scripts/3_folding/AlphaFold3/convert_output.py \
            {input.output_model}"/antibody/antibody_model.cif" \
            -o {params.output_pdb}
    """


rule prepare_haddock3:
    params:
        experiment_dir = config["main"]["experiment_dir"],
        antibody_pdb = config["docking"]["haddock3"]["antibody_pdb"],
        antigen_pdb = config["docking"]["haddock3"]["antigen_pdb"],
        prepared_antibody_pdb = config["docking"]["haddock3"]["prepared_antibody_pdb"],
        prepared_antigen_pdb = config["docking"]["haddock3"]["prepared_antigen_pdb"],
        air_file = config["docking"]["haddock3"]["air_file"],
        config_file = config["docking"]["haddock3"]["config_file"],
        n_cores=config["main"]["cores"]
    input:
        config["main"]["experiment_dir"]+"/4_docking/antibody.pdb"
    output: 
        config["main"]["experiment_dir"] + "/4_docking/" + config["docking"]["haddock3"]["config_file"]
    log:
        config["main"]["experiment_dir"] + "/frankies.log"
    shell: """
        ## Run antigen preparation
        python Scripts/4_docking/haddock3/prepare_antigen_inputs.py \
            --input_pdb_path {params.experiment_dir}/3_folding/{params.antigen_pdb} \
            --output_pdb_path {params.experiment_dir}/4_docking/{params.prepared_antigen_pdb} \
            --resn_offset 1000 \
            --percentage 0.25 && \

        ## Run antibody preparation
        python Scripts/4_docking/haddock3/prepare_antibody_inputs.py \
            --input_pdb_path {params.experiment_dir}/3_folding/{params.antibody_pdb} \
            --output_pdb_path {params.experiment_dir}/4_docking/{params.prepared_antibody_pdb} \
            --H_chain_id A \
            --L_chain_id B \
            --L_resn_offset 1000 && \

        ## Prepare experiment
        python Scripts/4_docking/haddock3/create_haddock_experiment.py \
            --experiment_path {params.experiment_dir}/4_docking \
            --antibody_pdb_path {params.experiment_dir}/4_docking/{params.prepared_antibody_pdb} \
            --antigen_pdb_path {params.experiment_dir}/4_docking/{params.prepared_antigen_pdb} \
            --active_antibody_path {params.experiment_dir}/4_docking/cdr_residues.txt \
            --active_antigen_path {params.experiment_dir}/4_docking/surface_residues.txt \
            --n_cores {params.n_cores} \
            --config_template_path Scripts/4_docking/haddock3/resources/antibody_antigen_template_custom.cfg
    """

# rule run_haddock3:
#     params:
#         experiment_dir=config["main"]["experiment_dir"],
#         config_file=config['docking']['haddock3']['config_file'],
#     input:
#         config_file=config["main"]["experiment_dir"] + "/4_docking/" + config['docking']['haddock3']['config_file'],
#     output:
#         config["main"]["experiment_dir"] + "/4_docking/HADDOCK_DONE"
#     shell: """
#         docker run -v {params.experiment_dir}/4_docking:/mnt/experiment --rm cford38/haddock:3 /bin/bash -c \
#             "cd /mnt/experiment && \
#             haddock3 {params.config_file} && \
#             touch HADDOCK_DONE"
#     """

# rule frank_dynamics:
#     input: "Scripts/4_docking/helloworld.txt"
#     output: "Scripts/5_dynamics/hello_world.txt"  
#     shell: "echo Hello World > Scripts/5_dynamics/hello_world.txt"

# rule frank_postprocess:
#     input: "Scripts/5_dynamics/hello_world.txt"  
#     output: "Scripts/6_postprocess/helloworld.txt"
#     shell: "echo Hello World > Scripts/6_postprocess/helloworld.txt"

