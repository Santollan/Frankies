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

## Host and Drivers
This was tested on:
 - Ubuntu 22.04 with NVIDIA 560 drivers and CUDA 12.6.
 - Windows Subsystem for Linux with Ubuntu 18.04 on an NVIDIA Titan X.