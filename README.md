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
