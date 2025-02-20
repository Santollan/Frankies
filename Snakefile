import os
configfile: "config.yaml"

rule all:
    input: "Scripts/6_postprocess/helloworld.txt"

rule frank_preprocess:
    output: "Scripts/1_preprocess/helloworld.txt"
    shell: "echo hello_frankie > Scripts/1_preprocess/helloworld.txt"

rule frank_diffusion:
    input: 
        prepare_evodiff= os.path.join(os.getcwd(), "Scripts/2_diffusion/prepare_evodiff.py"),
        Chain=config["Evo"]["H_Chain"]
    output: "Scripts/3_diffusion/helloworld.txt"
    shell: "conda activate evodiff && python3 {input.prepare_evodiff} --chain {input.Chain}" #this will need to trigger the prepare_evodiff.py

rule antigen_folding:
    input:
        seq=config["main"]["antigen"]["sequence"]
    output:
        structure=config["main"]["antigen"]["structure"] # Dynamic output path

    shell: """
        run_af3.sh --fasta_path {input.seq} --output_path {output.structure}
    """

rule frank_folding:
    input:
        seq=os.path.join(os.getcwd(), "data/processed/3_diffusion/af_input"),
        output_model=os.path.join(os.getcwd(), "outputs/3_diffusion")
    output:
        config["output"]["pdb"] # Dynamic output path
    shell: """      
        docker run -it \
            --volume {input.seq}:/root/af_input \
            --volume {input.output_model}:/root/af_output \
            --volume {config[alphafold][weights]}:/root/models \
            --volume {config[alphafold][databases]}:/root/public_databases \
            --gpus {config[gpus]} \
            alphafold3 \
            python run_alphafold.py \
            --json_path=/root/af_input/alphafold_input.json \
            --model_dir=/root/models \
            --output_dir=/root/af_output
    """



rule frank_docking:
    input: "Scripts/3_diffusion/helloworld.txt"
    output: "Scripts/4_docking/helloworld.txt"
    shell: "echo Hello World > Scripts/4_docking/helloworld.txt"

rule frank_dynamics:
    input: "Scripts/4_docking/helloworld.txt"
    output: "Scripts/5_dynamics/hello_world.txt"  
    shell: "echo Hello World > Scripts/5_dynamics/hello_world.txt"

rule frank_postprocess:
    input: "Scripts/5_dynamics/hello_world.txt"  
    output: "Scripts/6_postprocess/helloworld.txt"
    shell: "echo Hello World > Scripts/6_postprocess/helloworld.txt"

