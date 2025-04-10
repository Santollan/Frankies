# Frankies
Scalable, AI-Based Antibody Design Pipeline


## Setup Conda Environment
```bash
conda env create -f environment.yml
conda activate frankies

# conda env deactivate
# conda env update -n frankies -f environment.yml
```


## Run Snakemake Pipeline

Entire pipeline:
```bash
snakemake --snakefile Snakefile
```

Specific rule:
```bash
snakemake --force prepare_haddock3
```

## Host and Drivers
This was tested on:
 - Ubuntu 22.04 with NVIDIA 560 drivers and CUDA 12.6.
 - Windows Subsystem for Linux with Ubuntu 18.04 on an NVIDIA Titan X.