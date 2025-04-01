# EvoDiff Local Tests

## Docker
```sh
## Pull Image
docker pull cford38/evodiff:latest

## Run Docker Image (Bash Console)
docker run -v ./data:/mnt/data --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 --name evodiff --rm -it cford38/evodiff:latest /bin/bash

## Checkpoint Dir: /root/.cache/torch/hub/checkpoints/
```

## Run
```python
from evodiff.pretrained import MSA_OA_DM_MAXSUB
from evodiff.generate_msa import generate_query_oadm_msa_simple
import re
import torch
# torch.set_default_device('cuda:0')

checkpoint = MSA_OA_DM_MAXSUB()
model, collater, tokenizer, scheme = checkpoint

path_to_msa = '/mnt/data/inputs/anti-HA_antibodies_Hchains_aligned.fasta'
n_sequences=14 # number of sequences in MSA to subsample
seq_length=150 # maximum sequence length to subsample
selection_type='random' # or 'MaxHamming'; MSA subsampling scheme

## H Chain
tokenized_sample, generated_sequence  = generate_query_oadm_msa_simple(path_to_msa, model, tokenizer, n_sequences, seq_length, device=0, selection_type=selection_type)

print("New H chain sequence (no gaps, pad tokens)", re.sub('[!-]', '', generated_sequence[0][0],))
## ETQLQESGAGPKKVGPNLNLSSSTSGYTFSSYSYGWPVAREAPGQGLQKVGRIYPGAGYDTKYSESVKSRVFINIDTSKNTASLDLSTLTAEDTAVRMAARPGTYQVVGGGGGAGHSWVDPWGQBTLVTVSS

## L Chain
path_to_msa = '/mnt/data/inputs/anti-HA_antibodies_Lchains_aligned.fasta'
n_sequences=14 # number of sequences in MSA to subsample
seq_length=150 # maximum sequence length to subsample
selection_type='random' # or 'MaxHamming'; MSA subsampling scheme


tokenized_sample, generated_sequence  = generate_query_oadm_msa_simple(path_to_msa, model, tokenizer, n_sequences, seq_length, device=0, selection_type=selection_type)

print("New L chain sequence (no gaps, pad tokens)", re.sub('[!-]', '', generated_sequence[0][0],))
## DSVLTDSPSSLSVSPGARVTYSCRKSQSLVDSDSYNYVEWAYQQKPDJAPRLNIYDASPDATGVPAVFSDSGVGTEFTQTISRRADNLQPEAVAKYYAQQHNNDNNRWAKQTIEGGTKVEIKSKP
```
