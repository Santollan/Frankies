# Frankies
Scalable, AI-Based Antibody Design Pipeline


## Setup Conda Environment
```bash
conda env create -f environment.yml
conda activate frankies

# conda deactivate
# conda env update
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
This was tested on Ubuntu 22.04 with Nvidia 560 drivers and Cuda 12.6 