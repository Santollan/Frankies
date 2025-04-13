import os
configfile: "config.yaml"

rule all:
    input: 
        # "config_timestamp",
        config["main"]["experiment_dir"] + "/4_docking/output/10_caprieval/capri_ss.tsv" 
        # config["main"]["experiment_dir"] + "/5_postprocess/frankies_report.html",

# rule config_timestamp:
#     input:
#         config = "config.yaml"
#     output:
#         touch("config_timestamp")

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
        config["main"]["experiment_dir"] + "/1_inputs/" + config["main"]["H_chain"],
        config["main"]["experiment_dir"] + "/1_inputs/" + config["main"]["L_chain"],
        config["main"]["experiment_dir"] + "/1_inputs/" + config["main"]["Antigen"]
    run: 
        # Create the experiment directory
        shell("mkdir -p {params.experiment_dir}/1_inputs"),
        shell("cp -r ./data/inputs/* {params.experiment_dir}/1_inputs/"),
        # Create the output directories
        shell("mkdir -p {params.experiment_dir}/2_diffusion"),
        shell("mkdir -p {params.experiment_dir}/2_diffusion"),
        shell("mkdir -p {params.experiment_dir}/3_folding"),
        shell("mkdir -p {params.experiment_dir}/4_docking"),
        shell("echo \"Frankies pipeline started at: $(date)\" > {output}"),
        shell("docker info || echo 'Docker is not running. Please start Docker Desktop.'")
        shell("touch {params.experiment_dir}/2_diffusion/{params.H_chain}.json")
        shell("touch {params.experiment_dir}/3_folding/{params.H_chain}+{params.L_chain}.json"),
        shell("cp -r {params.experiment_dir}/1_inputs/{params.Antigen} {params.experiment_dir}/4_docking/antigen.pdb"),

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
        H_chain_file=config["main"]["experiment_dir"] + "/1_inputs/" + config["diffusion"]["evodiff"]["H_chain"],  # path to Hchain file
        L_chain_file=config["main"]["experiment_dir"] + "/1_inputs/" + config["diffusion"]["evodiff"]["L_chain"],  # path to Lchain file  
        H_chain_json=config["main"]["experiment_dir"]+"/2_diffusion/"+config["diffusion"]["evodiff"]["H_chain"]+".json",  # path to Hchain file
        L_chain_json=config["main"]["experiment_dir"]+"/2_diffusion/"+config["diffusion"]["evodiff"]["L_chain"]+".json",  # path to Lchain file
        prep_output_file=config["main"]["experiment_dir"]+"/3_folding/af_input/"+config["folding"]["alphafold3"]["prep_output_file_name"]
    input:
        Hchain_file=config["main"]["experiment_dir"] + "/1_inputs/" + config["diffusion"]["evodiff"]["H_chain"],  # path to Hchain file
    output:
        config["main"]["experiment_dir"]+"/3_folding/af_input/"+config["folding"]["alphafold3"]["prep_output_file_name"], # path to output file

    shell:
        """
        sudo docker run --gpus all --ipc=host --userns=host --ulimit memlock=-1 --ulimit stack=67108864 \
        -v $(pwd)/{params.experiment_dir}:/workspace/evodiff/frankie/experiment:rw \
        -v $(pwd)/scripts/2_diffusion:/workspace/evodiff/frankie:rw \
        -it --rm cford38/evodiff:v1.1.0 /bin/bash -c \
        "conda install -c bioconda abnumber -y && \
        python3 /workspace/evodiff/frankie/prepare_evodiff.py --path /workspace/evodiff/frankie/experiment/1_inputs/ --chain {params.H_chain} && \
        python3 /workspace/evodiff/frankie/prepare_evodiff.py --path /workspace/evodiff/frankie/experiment/1_inputs/ --chain {params.L_chain}" && \
        python3 scripts/3_folding/AlphaFold3/prepare_af3.py \
            --hchain_file {params.H_chain_json} \
            --lchain_file {params.L_chain_json} \
            --output_file {params.prep_output_file} 
        """

## Folding

# rule run_alphafold3:
#     # This rule runs AlphaFold3 using Docker with config-specified GPU settings
#     params:
#         experiment_dir = os.path.abspath(config["main"]["experiment_dir"]),
#         gpus = config["main"]["gpus"],
#         container_engine = config["main"]["container_engine"],
#         af3_input_dir = os.path.abspath(os.path.join(config["main"]["experiment_dir"], "3_folding", "af_input")),
#         output_pdb = os.path.abspath(os.path.join(config["main"]["experiment_dir"], "3_folding", "antibody.pdb")),
#         weights_dir = os.path.abspath(config["folding"]["alphafold3"]["weights_dir"]),
#         databases_dir = os.path.abspath(config["folding"]["alphafold3"]["databases_dir"]),
#         output_model_dir = os.path.abspath(os.path.join(config["main"]["experiment_dir"], "3_folding", "af_output")),
#     input:
#         alphafold_input = os.path.join(config["main"]["experiment_dir"], "3_folding/af_input", 
#                                        config["folding"]["alphafold3"]["prep_output_file_name"])
#     output:
#         pdb = os.path.join(config["main"]["experiment_dir"], "3_folding/antibody.pdb")
#     log:
#         os.path.join(config["main"]["experiment_dir"], "logs/alphafold3.log")
#     shell: 
#         """
#         # Create output directories
#         mkdir -p $(dirname {output.pdb})
#         mkdir -p {params.output_model_dir}
#         mkdir -p $(dirname {log})
        
#         echo "Starting AlphaFold3 run at $(date)" > {log}
#         echo "Using {params.container_engine} with GPU setting: {params.gpus}" >> {log}
#         echo "Using the following paths:" >> {log}
#         echo "Input directory: {params.af3_input_dir}" >> {log}
#         echo "Output directory: {params.output_model_dir}" >> {log}
#         echo "Weights directory: {params.weights_dir}" >> {log}
#         echo "Databases directory: {params.databases_dir}" >> {log}
        
#         # Check if AlphaFold3 image exists
#         if ! {params.container_engine} image inspect alphafold3 &>/dev/null; then
#             echo "ERROR: {params.container_engine} image 'alphafold3' does not exist!" >> {log}
#             echo "Please pull or build the AlphaFold3 image before running this step." >> {log}
#             exit 1
#         fi
        
#         # Set GPU flag based on config
#         if [ "{params.gpus}" = "all" ]; then
#             GPU_FLAG="--gpus all"
#         elif [ "{params.gpus}" = "none" ] || [ "{params.gpus}" = "" ]; then
#             GPU_FLAG=""
#         else
#             GPU_FLAG="--gpus {params.gpus}"
#         fi
        
#         echo "Using GPU flag: $GPU_FLAG" >> {log}
        
#         # Run AlphaFold3
#         echo "Running AlphaFold3..." >> {log}
#         ({params.container_engine} run --rm $GPU_FLAG \
#             --volume {params.af3_input_dir}:/root/af_input:ro \
#             --volume {params.output_model_dir}:/root/af_output:rw \
#             --volume {params.weights_dir}:/root/models:ro \
#             --volume {params.databases_dir}:/root/public_databases:ro \
#             alphafold3 \
#             python run_alphafold.py \
#                 --json_path=/root/af_input/alphafold_input.json \
#                 --model_dir=/root/models \
#                 --db_dir=/root/public_databases \
#                 --output_dir=/root/af_output) >> {log} 2>&1
        
#         # Check if the output file was created
#         if [ ! -f {params.output_model_dir}/antibody/antibody_model.cif ]; then
#             echo "ERROR: AlphaFold3 failed to create output model" >> {log}
#             ls -la {params.output_model_dir} >> {log} 2>&1
#             exit 1
#         fi
        
#         # Convert output
#         echo "Converting output to PDB format..." >> {log}
#         (python3 ./scripts/3_folding/AlphaFold3/convert_output.py \
#             {params.output_model_dir}/antibody/antibody_model.cif \
#             -o {output.pdb}) >> {log} 2>&1
        
#         echo "AlphaFold3 run completed at $(date)" >> {log}
#         """

rule run_esmfold:
    params:
        experiment_dir = config["main"]["experiment_dir"],
        token = config["folding"]["esmfold"]["forge_token"],
        model = config["folding"]["esmfold"]["model"]
    input:
        input_h_json = config["main"]["experiment_dir"] + "/2_diffusion/anti-HA_antibodies_Hchains_aligned.a3m.json",
        input_l_json = config["main"]["experiment_dir"] + "/2_diffusion/anti-HA_antibodies_Lchains_aligned.a3m.json",
    output:
        output_pdb = config["main"]["experiment_dir"] + "/3_folding/antibody.pdb"
    shell:
        """
        ## Create output directories
        mkdir -p $(dirname {output.output_pdb})

        ## Run ESMFold
        python3 scripts/3_folding/ESM3/run_esmfold.py \
            --input_h_json {input.input_h_json} \
            --input_l_json {input.input_l_json} \
            --token {params.token} \
            --model {params.model} \
            --output_pdb {output.output_pdb}
        """

## Docking
rule prepare_haddock3:
    params:
        experiment_dir = config["main"]["experiment_dir"],
        antibody_pdb = "antibody.pdb",
        antigen_pdb = config["main"]["Antigen"],
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
    shell:
        """
        ## Run antigen preparation
        python scripts/4_docking/haddock3/prepare_antigen_inputs.py \
            --input_pdb_path {params.experiment_dir}/1_inputs/{params.antigen_pdb} \
            --output_pdb_path {params.experiment_dir}/4_docking/{params.prepared_antigen_pdb} \
            --resn_offset 1000 \
            --percentage 0.25 && \

        ## Run antibody preparation
        python scripts/4_docking/haddock3/prepare_antibody_inputs.py \
            --input_pdb_path {params.experiment_dir}/3_folding/{params.antibody_pdb} \
            --output_pdb_path {params.experiment_dir}/4_docking/{params.prepared_antibody_pdb} \
            --H_chain_id A \
            --L_chain_id B \
            --L_resn_offset 1000 && \

        ## Prepare experiment
        python scripts/4_docking/haddock3/create_haddock_experiment.py \
            --experiment_path {params.experiment_dir}/4_docking \
            --antibody_pdb_path {params.experiment_dir}/4_docking/{params.prepared_antibody_pdb} \
            --antigen_pdb_path {params.experiment_dir}/4_docking/{params.prepared_antigen_pdb} \
            --active_antibody_path {params.experiment_dir}/4_docking/cdr_residues.txt \
            --active_antigen_path {params.experiment_dir}/4_docking/surface_residues.txt \
            --n_cores {params.n_cores} \
            --config_template_path scripts/4_docking/haddock3/resources/antibody_antigen_template_custom.cfg
        """

## Docking
rule run_haddock3:
    params:
        experiment_dir=config["main"]["experiment_dir"],
        config_file=config['docking']['haddock3']['config_file'],
    input:
        config_file=config["main"]["experiment_dir"] + "/4_docking/" + config['docking']['haddock3']['config_file'],
    output:
        config["main"]["experiment_dir"] + "/4_docking/output/10_caprieval/capri_clt.tsv",
        config["main"]["experiment_dir"] + "/4_docking/output/10_caprieval/capri_ss.tsv"
    shell:
        """
        docker run -v $(pwd)/{params.experiment_dir}/4_docking:/mnt/experiment --rm cford38/haddock:3 /bin/bash -c \
            "cd /mnt/experiment && \
            haddock3 {params.config_file}"
        """

## Report Generation
rule make_report:
    params:
        experiment_dir = config["main"]["experiment_dir"],
        experiment_name = config["main"]["experiment_name"]
    input:
        haddock_clt_file = config["main"]["experiment_dir"] + "/4_docking/output/10_caprieval/capri_clt.tsv",
        haddock_ss_file = config["main"]["experiment_dir"] + "/4_docking/output/10_caprieval/capri_clt.tsv",
        input_h_json = config["main"]["experiment_dir"] + "/2_diffusion/anti-HA_antibodies_Hchains_aligned.a3m.json",
        input_l_json = config["main"]["experiment_dir"] + "/2_diffusion/anti-HA_antibodies_Lchains_aligned.a3m.json"
    output:
        output_report = config["main"]["experiment_dir"] + "/5_postprocess/frankies_report.html"
    shell:
        """
        ## Create output directories
        mkdir -p $(dirname {output.output_report})
        cp scripts/5_postprocess/frankies_report.qmd {params.experiment_dir}/5_postprocess/frankies_report.qmd
        cp scripts/5_postprocess/frankies.scss {params.experiment_dir}/5_postprocess/frankies.scss

        ## Render dashboard with Quarto
        quarto render $(pwd)/{params.experiment_dir}/5_postprocess/frankies_report.qmd \
            -P experiment_dir:$(pwd)/{params.experiment_dir} \
            -P capri_clt_file:$(pwd)/{input.haddock_clt_file} \
            -P capri_ss_file:$(pwd)/{input.haddock_ss_file} \
            -P input_h_json:$(pwd)/{input.input_h_json} \
            -P input_l_json:$(pwd)/{input.input_l_json} \
        """