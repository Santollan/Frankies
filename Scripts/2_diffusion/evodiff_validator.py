#!/usr/bin/env python3
"""
EvoDiff Sequence Generator with Validation

This script generates antibody sequences using EvoDiff's MSA model
and validates them using the abnumber Chain class.

Features:
- Uses GPU if available
- Generates multiple sequences and validates them
- Performs comprehensive cleaning and validation
- Provides detailed reports on sequence validity
"""

import re
import os
import time
import torch
import logging
from tqdm import tqdm
from abnumber import Chain

# Import EvoDiff modules
from evodiff.pretrained import MSA_OA_DM_MAXSUB
from evodiff.generate_msa import generate_query_oadm_msa_simple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='sequence_generation.log'
)
logger = logging.getLogger(__name__)

def clean_sequence(seq):
    """
    Clean the sequence by:
    1. Removing ! and - characters
    2. Replacing Z with G
    3. Replacing B with G
    4. Replacing J with L
    5. Replacing any other non-standard amino acids with G
    """
    logger.info("Cleaning sequence")
    # Remove ! and - characters
    seq = re.sub('[!-]', '', seq)
    # Replace Z, B with G and J with L
    seq = seq.replace('Z', 'G')
    seq = seq.replace('B', 'G')
    seq = seq.replace('J', 'L')
    
    # Replace any other non-standard amino acids with G
    standard_aas = set('ACDEFGHIKLMNPQRSTVWY')
    cleaned = ''.join([aa if aa in standard_aas else 'G' for aa in seq])
    
    return cleaned

def analyze_sequence(seq):
    """Perform a detailed analysis of a sequence"""
    # Check if it looks like a heavy or light chain based on the start
    chain_type = "unknown"
    if seq.startswith(("EVQ", "QVQ", "ETQ")):
        chain_type = "heavy (VH)"
    elif seq.startswith(("DIV", "DIQ", "DSV", "EIV")):
        chain_type = "light (VL)"
    
    return {
        'length': len(seq),
        'likely_chain_type': chain_type
    }

def validate_sequence(seq, schemes=None):
    """
    Validate if a sequence can be parsed by abnumber Chain.
    
    Args:
        seq (str): The sequence to validate
        schemes (list): List of numbering schemes to try
        
    Returns:
        tuple: (bool, dict) - (is_valid, validation_results)
    """
    if schemes is None:
        schemes = ['chothia', 'imgt', 'kabat', 'martin', 'aho', 'imgt_gap']
    
    # Check for non-standard amino acids
    standard_aas = set('ACDEFGHIKLMNPQRSTVWY')
    non_standard = [(i, aa) for i, aa in enumerate(seq) if aa not in standard_aas]
    
    results = {
        'sequence': seq,
        'non_standard_aas': non_standard,
        'validations': {}
    }
    
    # Try each numbering scheme
    any_valid = False
    valid_chain = None
    
    for scheme in schemes:
        try:
            chain = Chain(seq, scheme=scheme)
            results['validations'][scheme] = {
                'valid': True,
                'chain': chain
            }
            any_valid = True
            valid_chain = chain
        except Exception as e:
            results['validations'][scheme] = {
                'valid': False,
                'error': str(e)
            }
    
    return any_valid, valid_chain, results

def print_validation_results(results):
    """Print validation results in a readable format"""
    print(f"Sequence: {results['sequence']}")
    
    analysis = analyze_sequence(results['sequence'])
    print(f"Length: {analysis['length']} amino acids")
    print(f"Likely chain type: {analysis['likely_chain_type']}")
    
    if results['non_standard_aas']:
        print("\nNon-standard amino acids detected:")
        for pos, aa in results['non_standard_aas']:
            print(f"  Position {pos+1}: {aa}")
    
    print("\nValidation results:")
    for scheme, result in results['validations'].items():
        if result['valid']:
            print(f"  {scheme}: Valid ✓")
        else:
            print(f"  {scheme}: Invalid ✗ - {result['error']}")
    
    # Overall verdict
    valid_schemes = [s for s, r in results['validations'].items() if r['valid']]
    if valid_schemes:
        print(f"\nVERDICT: VALID with schemes: {', '.join(valid_schemes)}")
    else:
        print("\nVERDICT: INVALID with all schemes")

def generate_and_validate(max_attempts=20):
    """
    Generate and validate sequences using EvoDiff
    """
    # Check if GPU is available and set device
    if torch.cuda.is_available():
        device = 0  # Use first GPU
        logger.info(f"Using GPU: {torch.cuda.get_device_name(device)}")
        # Uncomment to set default device
        # torch.set_default_device(f'cuda:{device}')
    else:
        device = 'cpu'
        logger.info("GPU not available, using CPU")
    
    # Load model checkpoint
    logger.info("Loading model checkpoint")
    checkpoint = MSA_OA_DM_MAXSUB()
    model, collater, tokenizer, scheme = checkpoint
    logger.info("Model checkpoint loaded successfully")
    
    # Path to MSA file
    path_to_msa = '/mnt/data/inputs/anti-HA_antibodies_Hchains_aligned.fasta'
    if not os.path.exists(path_to_msa):
        logger.error(f"MSA file not found at {path_to_msa}. Cannot continue.")
        return [], []
    
    # Parameters
    n_sequences = 14  # number of sequences in MSA to subsample
    seq_length = 150  # maximum sequence length to subsample
    selection_type = 'random'  # or 'MaxHamming'; MSA subsampling scheme
    
    valid_sequences = []
    invalid_sequences = []
    
    logger.info(f"Starting sequence generation and validation. Will attempt up to {max_attempts} times.")
    
    for attempt in tqdm(range(max_attempts), desc="Generating sequences"):
        logger.info(f"Attempt {attempt+1}/{max_attempts}")
        
        # Generate sequence
        try:
            tokenized_sample, generated_sequence = generate_query_oadm_msa_simple(
                path_to_msa, model, tokenizer, n_sequences, seq_length, 
                device=device, selection_type=selection_type
            )
            
            # Extract and clean the sequence
            raw_seq = generated_sequence[0][0]
            logger.info(f"Raw sequence: {raw_seq}")
            clean_seq = clean_sequence(raw_seq)
            logger.info(f"Cleaned sequence: {clean_seq}")
            
            # Validate the sequence
            is_valid, chain, validation_results = validate_sequence(clean_seq)
            
            if is_valid:
                logger.info(f"Valid sequence found on attempt {attempt+1}")
                valid_sequences.append((clean_seq, chain, validation_results))
                print(f"\n=== Valid sequence #{len(valid_sequences)} (Attempt {attempt+1}) ===")
                print_validation_results(validation_results)
            else:
                invalid_sequences.append((clean_seq, validation_results))
                logger.info(f"Invalid sequence on attempt {attempt+1}")
                print(f"\n=== Invalid sequence (Attempt {attempt+1}) ===")
                print_validation_results(validation_results)
            
        except Exception as e:
            logger.error(f"Error during generation attempt {attempt+1}: {str(e)}")
            continue
    
    # Final results summary
    logger.info(f"Generation complete. Found {len(valid_sequences)} valid sequences out of {max_attempts} attempts.")
    print(f"\n=== Generation complete ===")
    print(f"Found {len(valid_sequences)} valid sequences out of {max_attempts} attempts.")
    
    if valid_sequences:
        print("\nAll valid sequences:")
        for i, (seq, chain, _) in enumerate(valid_sequences, 1):
            print(f"{i}. {seq}")
            print(f"   Chain: {chain}")
            print()
    
    return valid_sequences, invalid_sequences

def main():
    start_time = time.time()
    valid_seqs, invalid_seqs = generate_and_validate(max_attempts=20)
    elapsed_time = time.time() - start_time
    
    logger.info(f"Total execution time: {elapsed_time:.2f} seconds")
    print(f"\nTotal execution time: {elapsed_time:.2f} seconds")
    
    # Save valid sequences to a file
    if valid_seqs:
        with open('valid_sequences.txt', 'w') as f:
            for i, (seq, chain, _) in enumerate(valid_seqs, 1):
                f.write(f">Valid_sequence_{i}\n{seq}\n")
        print(f"Saved {len(valid_seqs)} valid sequences to valid_sequences.txt")
    
    # Print the log file contents
    print("\nLog file contents:")
    try:
        with open('sequence_generation.log', 'r') as log_file:
            print(log_file.read())
    except Exception as e:
        print(f"Could not read log file: {str(e)}")

if __name__ == "__main__":
    main()