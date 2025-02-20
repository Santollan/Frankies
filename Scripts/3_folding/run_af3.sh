
python prepare_sf3_json.py --fasta_path "" --output_path fold_input.json


docker run -it \
    --volume $PWD/data/processed/3_diffusion/af_input:/root/af_input \
    --volume $PWD/data/processed/3_diffusion/af_output :/root/af_output \
    --volume /media/ssd2/Projects/Alphafold/Alphafold_weights :/root/models \
    --volume /media/ssd2/Projects/Alphafold/Alphafold_DB :/root/public_databases \
    --gpus all \
    alphafold3 \
    python run_alphafold.py \
    --json_path=/root/af_input/fold_input.json \
    --model_dir=/root/models \
    --output_dir=/root/af_output