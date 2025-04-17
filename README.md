# Frankies
Scalable, AI-Based Antibody Design Pipeline


## Setup Conda Environment
```bash
conda env create -f environment.yml
conda activate frankies

# conda deactivate
# conda env update -n frankies -f environment.yml
```

> [!NOTE]  
> You'll also need to install Quarto separately. See https://quarto.org/docs/get-started/ for instructions.


## Run Snakemake Pipeline

Entire pipeline:
```bash
snakemake --snakefile Snakefile
```

Specific rule:
```bash
snakemake --force make_report
```

Clear current experiment name:
```bash
rm .current_experiment_name
```

## Run Batch of Snakemake Pipeline
```bash
./run_snakemake_multiple.sh
```
By default, this will run the pipeline 10 times and create a new experiment name each time. You can change the number of runs by modifying the `NUM_RUNS` variable in the script.

## Host and Drivers
This was tested on:
 - Ubuntu 22.04 with NVIDIA 560 drivers and CUDA 12.6.
 - Windows Subsystem for Linux with Ubuntu 18.04 on an NVIDIA Titan X.