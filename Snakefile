import os
configfile: "config.yaml"

rule config_timestamp:
    input:
        config = "config.yaml"
    output:
        touch("config_timestamp")

rule all:
    input: 
        "config_timestamp",

rule initialize:
    input:
        config_stamp = "config_timestamp"
    params:
        experiment_dir = config["main"]["experiment_dir"],
        experiment_name = config["main"]["experiment_name"],
        H_chain = config["main"]["H_chain"],
        L_chain = config["main"]["L_chain"],
        Antigen = config["main"]["Antigen"],
    output:
        config["main"]["experiment_dir"] + "/frankies.log",
        config["main"]["experiment_dir"] + "/01_inputs/" + config["main"]["H_chain"],
        config["main"]["experiment_dir"] + "/01_inputs/" + config["main"]["L_chain"],
        config["main"]["experiment_dir"] + "/01_inputs/" + config["main"]["Antigen"]
    run: 
        # Create the experiment directory
        shell("mkdir -p {params.experiment_dir}/01_inputs"),
        shell("cp -r ./data/inputs/* {params.experiment_dir}/01_inputs/"),
        # Create the output directories
        shell("mkdir -p {params.experiment_dir}/2_diffusion"),
        shell("mkdir -p {params.experiment_dir}/2_diffusion"),
        shell("mkdir -p {params.experiment_dir}/3_folding"),
        shell("mkdir -p {params.experiment_dir}/4_docking"),
        shell("echo \"Frankies pipeline started at: $(date)\" > {output}"),
        shell("docker info || echo 'Docker is not running. Please start Docker Desktop.'")

# rule frank_preprocess:
#     output: "Scripts/1_preprocess/helloworld.txt"
#     shell: "echo hello_frankie > Scripts/1_preprocess/helloworld.txt"
rule run_evodiff:
    params:
        experiment_dir = "$(pwd)/" + config["main"]["experiment_dir"],  # Use shell expansion
        scripts_dir = "$(pwd)/Scripts/2_diffusion",
        H_chain = config["diffusion"]["evodiff"]["H_chain"],
        L_chain = config["diffusion"]["evodiff"]["L_chain"]
    input:
        Hchain_file = os.path.join(config["main"]["experiment_dir"], "01_inputs", config["diffusion"]["evodiff"]["H_chain"]),
        Lchain_file = os.path.join(config["main"]["experiment_dir"], "01_inputs", config["diffusion"]["evodiff"]["L_chain"])
    output:
        alphafold_input = os.path.join(config["main"]["experiment_dir"], "3_folding/af_input", config["folding"]["alphafold3"]["prep_output_file_name"]),
        h_json = os.path.join(config["main"]["experiment_dir"], "2_diffusion", config["diffusion"]["evodiff"]["H_chain"] + ".json"),
        l_json = os.path.join(config["main"]["experiment_dir"], "2_diffusion", config["diffusion"]["evodiff"]["L_chain"] + ".json")
    log:
        os.path.join(config["main"]["experiment_dir"], "logs", "evodiff.log")
    shell:
        """
        # Create output directories
        mkdir -p $(dirname {output.alphafold_input})
        mkdir -p $(dirname {output.h_json})
        mkdir -p $(dirname {log})
        
        echo "Starting EvoDiff processing at $(date)" > {log}
        
        # Process H chain
        echo "Processing H chain: {params.H_chain}" >> {log}
        docker run \
            -v {params.experiment_dir}:/workspace/evodiff/frankie/experiment:rw \
            -v {params.scripts_dir}:/workspace/evodiff/frankie:rw \
            --rm cford38/evodiff:v1.1.0 /bin/bash -c \
            "conda install -c bioconda abnumber -y && \
            python3 /workspace/evodiff/frankie/prepare_evodiff.py --path /workspace/evodiff/frankie/experiment/01_inputs/ --chain {params.H_chain}" >> {log} 2>&1
        
        # Check if H chain JSON was created
        if [ ! -f {output.h_json} ]; then
          echo "ERROR: H chain JSON file was not created" >> {log}
          exit 1
        fi
        
        # Process L chain
        echo "Processing L chain: {params.L_chain}" >> {log}
        docker run \
            -v {params.experiment_dir}:/workspace/evodiff/frankie/experiment:rw \
            -v {params.scripts_dir}:/workspace/evodiff/frankie:rw \
            --rm cford38/evodiff:v1.1.0 /bin/bash -c \
            "python3 /workspace/evodiff/frankie/prepare_evodiff.py --path /workspace/evodiff/frankie/experiment/01_inputs/ --chain {params.L_chain}" >> {log} 2>&1
          
        # Check if L chain JSON was created
        if [ ! -f {output.l_json} ]; then
          echo "ERROR: L chain JSON file was not created" >> {log}
          exit 1
        fi
        
        # Run AlphaFold3 preparation
        echo "Preparing AlphaFold3 input" >> {log}
        python3 Scripts/3_folding/AlphaFold3/prepare_af3.py \
          --hchain_file {output.h_json} \
          --lchain_file {output.l_json} \
          --output_file {output.alphafold_input} >> {log} 2>&1
        """
# rule run_evodiff:
#     params:
#         experiment_dir=config["main"]["experiment_dir"],
#         exeriment_name=config["main"]["experiment_name"],
#         container_engine=config["main"]["container_engine"],
#         H_chain=config["diffusion"]["evodiff"]["H_chain"],
#         L_chain=config["diffusion"]["evodiff"]["L_chain"],
#         H_chain_file=config["main"]["experiment_dir"] + "/01_inputs/" + config["diffusion"]["evodiff"]["H_chain"],  # path to Hchain file
#         L_chain_file=config["main"]["experiment_dir"] + "/01_inputs/" + config["diffusion"]["evodiff"]["L_chain"],  # path to Lchain file  
#         H_chain_json=config["main"]["experiment_dir"]+"/2_diffusion/"+config["diffusion"]["evodiff"]["H_chain"]+".json",  # path to Hchain file
#         L_chain_json=config["main"]["experiment_dir"]+"/2_diffusion/"+config["diffusion"]["evodiff"]["L_chain"]+".json",  # path to Lchain file
#         prep_output_file=config["main"]["experiment_dir"]+"/3_folding/af_input/"+config["folding"]["alphafold3"]["prep_output_file_name"]
#     input:
#         Hchain_file=config["main"]["experiment_dir"] + "/01_inputs/" + config["diffusion"]["evodiff"]["H_chain"],  # path to Hchain file
#     output:
#         config["main"]["experiment_dir"]+"/3_folding/af_input/"+config["folding"]["alphafold3"]["prep_output_file_name"], # path to output file

#     shell:
#         """
# sudo docker run --gpus all --ipc=host --userns=host --ulimit memlock=-1 --ulimit stack=67108864 \
#   -v {params.experiment_dir}:/workspace/evodiff/frankie/experiment:rw \
#   -v ./Scripts/2_diffusion:/workspace/evodiff/frankie:rw \
#   -it --rm cford38/evodiff:v1.1.0 /bin/bash -c \
#   "conda install -c bioconda abnumber -y && \
#   python3 /workspace/evodiff/frankie/prepare_evodiff.py --path /workspace/evodiff/frankie/experiment/01_inputs/ --chain {params.H_chain} && \
#    python3 /workspace/evodiff/frankie/prepare_evodiff.py --path /workspace/evodiff/frankie/experiment/01_inputs/ --chain {params.L_chain}" && \
#     python3 Scripts/3_folding/AlphaFold3/prepare_af3.py \
#         --hchain_file {params.H_chain_json} \
#         --lchain_file {params.L_chain_json} \
#         --output_file {params.prep_output_file} 
#    """



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
rule run_alphafold3:
    # This rule runs AlphaFold3 using Docker with config-specified GPU settings
    params:
        experiment_dir = config["main"]["experiment_dir"],
        gpus = config["main"]["gpus"],
        container_engine = config["main"]["container_engine"],
        af3_input_dir = os.path.join(config["main"]["experiment_dir"], "3_folding/af_input"),
        output_pdb = os.path.join(config["main"]["experiment_dir"], "3_folding/antibody.pdb"),
        weights_dir = config["folding"]["alphafold3"]["weights_dir"],
        databases_dir = config["folding"]["alphafold3"]["databases_dir"],
        output_model_dir = os.path.join(config["main"]["experiment_dir"], "3_folding/af_output")
    input:
        alphafold_input = os.path.join(config["main"]["experiment_dir"], "3_folding/af_input", 
                                       config["folding"]["alphafold3"]["prep_output_file_name"])
    output:
        pdb = os.path.join(config["main"]["experiment_dir"], "3_folding/antibody.pdb")
    log:
        os.path.join(config["main"]["experiment_dir"], "logs/alphafold3.log")
    shell: 
        """
        # Create output directories
        mkdir -p $(dirname {output.pdb})
        mkdir -p {params.output_model_dir}
        mkdir -p $(dirname {log})
        
        echo "Starting AlphaFold3 run at $(date)" > {log}
        echo "Using {params.container_engine} with GPU setting: {params.gpus}" >> {log}
        echo "Using the following paths:" >> {log}
        echo "Input directory: {params.af3_input_dir}" >> {log}
        echo "Output directory: {params.output_model_dir}" >> {log}
        echo "Weights directory: {params.weights_dir}" >> {log}
        echo "Databases directory: {params.databases_dir}" >> {log}
        
        # Check if AlphaFold3 image exists
        if ! {params.container_engine} image inspect alphafold3 &>/dev/null; then
            echo "ERROR: {params.container_engine} image 'alphafold3' does not exist!" >> {log}
            echo "Please pull or build the AlphaFold3 image before running this step." >> {log}
            exit 1
        fi
        
        # Set GPU flag based on config
        if [ "{params.gpus}" = "all" ]; then
            GPU_FLAG="--gpus all"
        elif [ "{params.gpus}" = "none" ] || [ "{params.gpus}" = "" ]; then
            GPU_FLAG=""
        else
            GPU_FLAG="--gpus {params.gpus}"
        fi
        
        echo "Using GPU flag: $GPU_FLAG" >> {log}
        
        # Run AlphaFold3
        echo "Running AlphaFold3..." >> {log}
        ({params.container_engine} run --rm $GPU_FLAG \
            --volume {params.af3_input_dir}:/root/af_input:ro \
            --volume {params.output_model_dir}:/root/af_output:rw \
            --volume {params.weights_dir}:/root/models:ro \
            --volume {params.databases_dir}:/root/public_databases:ro \
            alphafold3 \
            python run_alphafold.py \
                --json_path=/root/af_input/alphafold_input.json \
                --model_dir=/root/models \
                --db_dir=/root/public_databases \
                --output_dir=/root/af_output) >> {log} 2>&1
        
        # Check if the output file was created
        if [ ! -f {params.output_model_dir}/antibody/antibody_model.cif ]; then
            echo "ERROR: AlphaFold3 failed to create output model" >> {log}
            ls -la {params.output_model_dir} >> {log} 2>&1
            exit 1
        fi
        
        # Convert output
        echo "Converting output to PDB format..." >> {log}
        (python3 ./Scripts/3_folding/AlphaFold3/convert_output.py \
            {params.output_model_dir}/antibody/antibody_model.cif \
            -o {output.pdb}) >> {log} 2>&1
        
        echo "AlphaFold3 run completed at $(date)" >> {log}
        """
# rule run_alphafold3:
#     # This rule runs AlphaFold3 using Docker
#     params:
#         experiment_dir=config["main"]["experiment_dir"],
#         af3_input_dir=config["main"]["experiment_dir"]+"/3_folding/af_input",
#         output_pdb=config["main"]["experiment_dir"]+"/3_folding/antibody.pdb"
#     input:
#         config["main"]["experiment_dir"]+"/3_folding/af_input/"+config["folding"]["alphafold3"]["prep_output_file_name"], # path to AlphaFold3 input file
#         output_model=config["main"]["experiment_dir"]+"/3_folding/af_output",
#         weights_dir=config["folding"]["alphafold3"]["weights_dir"],
#         databases_dir=config["folding"]["alphafold3"]["databases_dir"],
 
#     output:
#         config["main"]["experiment_dir"]+"/3_folding/antibody.pdb" # path to output file
#     shell: """
#         docker run --rm -it \
#             --volume {params.af3_input_dir}:/root/af_input \
#             --volume {input.output_model}:/root/af_output \
#             --volume {input.weights_dir}:/root/models \
#             --volume {input.databases_dir}:/root/public_databases \
#             --gpus all \
#             alphafold3 \
#             python run_alphafold.py \
#             --json_path=/root/af_input/alphafold_input.json \
#             --model_dir=/root/models \
#             --db_dir=/root/public_databases \
#             --db_dir=/root/public_databases_fallback \
#             --output_dir=/root/af_output && \
#         python3 ./Scripts/3_folding/AlphaFold3/convert_output.py \
#             {input.output_model}"/antibody/antibody_model.cif" \
#             -o {params.output_pdb}
#     """


rule prepare_haddock3:
    params:
        experiment_dir = config["main"]["experiment_dir"],
        antibody_pdb = "antibody.pdb",
        antigen_pdb = "antigen.pdb",
        prepared_antibody_pdb = config["docking"]["haddock3"]["prepared_antibody_pdb"],
        prepared_antigen_pdb = config["docking"]["haddock3"]["prepared_antigen_pdb"],
        air_file = config["docking"]["haddock3"]["air_file"],
        config_file = config["docking"]["haddock3"]["config_file"],
        n_cores=config["main"]["cores"]
    input:
        config["main"]["experiment_dir"]+"/3_folding/antibody.pdb"
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

rule run_haddock3:
    params:
        experiment_dir=config["main"]["experiment_dir"],
        config_file=config['docking']['haddock3']['config_file'],
    input:
        config_file=config["main"]["experiment_dir"] + "/4_docking/" + config['docking']['haddock3']['config_file'],
    output:
        config["main"]["experiment_dir"] + "/4_docking/HADDOCK_DONE"
    shell: """
        docker run -v {params.experiment_dir}/4_docking:/mnt/experiment --rm cford38/haddock:3 /bin/bash -c \
            "cd /mnt/experiment && \
            haddock3 {params.config_file} && \
            touch HADDOCK_DONE"
    """

rule frank_dynamics:
    input: "Scripts/4_docking/helloworld.txt"
    output: "Scripts/5_dynamics/hello_world.txt"  
    shell: "echo Hello World > Scripts/5_dynamics/hello_world.txt"

rule frank_postprocess:
    input: "Scripts/5_dynamics/hello_world.txt"  
    output: "Scripts/6_postprocess/helloworld.txt"
    shell: "echo Hello World > Scripts/6_postprocess/helloworld.txt"

