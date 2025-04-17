#!/usr/bin/env python3
"""
Antibody Sequence Generator with Validation

This script combines sequence generation from EvoDiff with robust validation
and simplified input/output handling.
"""

import re
import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Tuple, Optional, Any, Union

import torch
from abnumber import Chain
sys.path.append('/workspace/evodiff')  # Add explicit path to evodiff
# Import EvoDiff modules
from evodiff.pretrained import MSA_OA_DM_MAXSUB
from evodiff.generate_msa import generate_query_oadm_msa_simple



# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sequence_generation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def clean_sequence(seq: str) -> str:
    """
    Clean the sequence by removing non-standard amino acids.
    
    Args:
        seq: Raw protein sequence
        
    Returns:
        Cleaned protein sequence
    """
    # Remove ! and - characters
    seq = re.sub('[!-]', '', seq)
    
    # Replace non-standard amino acids
    replacements = {
        'Z': 'G',
        'B': 'G',
        'J': 'L',
        'X': 'G',
        'U': 'G',
        'O': 'G'
    }
    
    for old, new in replacements.items():
        seq = seq.replace(old, new)
    
    # Replace any other non-standard amino acids with G
    standard_aas = set('ACDEFGHIKLMNPQRSTVWY')
    cleaned = ''.join([aa if aa in standard_aas else 'G' for aa in seq])
    
    return cleaned


def analyze_sequence(seq: str) -> Dict[str, Any]:
    """
    Perform a detailed analysis of an antibody sequence.
    
    Args:
        seq: Protein sequence
        
    Returns:
        Dictionary with sequence properties
    """
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


def validate_sequence(seq: str, schemes: Optional[List[str]] = None) -> Tuple[bool, Optional[Chain], Dict[str, Any]]:
    """
    Validate if a sequence can be parsed by abnumber Chain.
    
    Args:
        seq: The sequence to validate
        schemes: List of numbering schemes to try
        
    Returns:
        Tuple containing (is_valid, chain_object, validation_results)
    """
    if schemes is None:
        schemes = ['chothia', 'imgt', 'kabat']
    
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
                'chain_type': str(chain.chain_type) if hasattr(chain, 'chain_type') else 'unknown'
            }
            any_valid = True
            valid_chain = chain
        except Exception as e:
            results['validations'][scheme] = {
                'valid': False,
                'error': str(e)
            }
    
    return any_valid, valid_chain, results


def format_validation_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format validation results for JSON output.
    
    Args:
        results: Raw validation results
        
    Returns:
        Formatted results dictionary
    """
    analysis = analyze_sequence(results['sequence'])
    
    formatted = {
        'sequence': results['sequence'],
        'length': analysis['length'],
        'likely_chain_type': analysis['likely_chain_type'],
        'non_standard_aas': [{'position': pos+1, 'aa': aa} for pos, aa in results['non_standard_aas']],
        'validation_schemes': {}
    }
    
    for scheme, result in results['validations'].items():
        formatted['validation_schemes'][scheme] = {
            'valid': result['valid'],
            'message': result.get('chain_type', '') if result['valid'] else result.get('error', '')
        }
    
    # Overall verdict
    valid_schemes = [s for s, r in results['validations'].items() if r['valid']]
    formatted['valid'] = bool(valid_schemes)
    formatted['valid_schemes'] = valid_schemes
    
    return formatted


def main():
    """Main function to run the script"""
    parser = argparse.ArgumentParser(description="Generate and validate antibody sequences")
    parser.add_argument("--sequence_count", type=int, default=14, 
                       help="The number of sequences in MSA subsample")
    parser.add_argument("--max_sequence", type=int, default=150, 
                       help="Maximum sequence length to subsample")
    parser.add_argument("--path", type=str, required=True,
                       help="The directory path containing the MSA file")
    parser.add_argument("--chain", type=str, required=True,
                       help="The filename of the MSA file")
    parser.add_argument("--output_dir", type=str, default="./output",
                       help="Directory to save output files")
    parser.add_argument("--device", type=str, default="cpu",
                       help="Device to use for generation (cpu or cuda:N)")
    parser.add_argument("--selection_type", type=str, default="random",
                       choices=["random", "MaxHamming"],
                       help="MSA subsampling scheme")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Set device
    if args.device != "cpu" and not torch.cuda.is_available():
        logger.warning("CUDA not available, defaulting to CPU")
        args.device = "cpu"
    
    try:
        torch.set_default_device(args.device)
        logger.info(f"Using device: {args.device}")
    except Exception as e:
        logger.warning(f"Could not set default device: {e}")
    
    # Construct path to MSA file
    path_to_msa = os.path.join(args.path, args.chain)
    
    if not os.path.exists(path_to_msa):
        logger.error(f"MSA file not found at {path_to_msa}")
        exit(1)
    
    logger.info(f"Loading the EvoDiff model for {args.chain}")
    try:
        checkpoint = MSA_OA_DM_MAXSUB()
        model, collater, tokenizer, scheme = checkpoint
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        exit(1)
    
    # Generate sequence
    logger.info(f"Generating sequence from {path_to_msa}")
    logger.info(f"Parameters: n_sequences={args.sequence_count}, seq_length={args.max_sequence}")
    
    try:
        tokenized_sample, generated_sequence = generate_query_oadm_msa_simple(
            path_to_msa, model, tokenizer, args.sequence_count, args.max_sequence,
            device=args.device, selection_type=args.selection_type
        )
        
        # Extract and clean the generated sequence
        raw_seq = generated_sequence[0][0]
        logger.info(f"Raw sequence generated: {raw_seq}")
        
        clean_seq = clean_sequence(raw_seq)
        logger.info(f"Cleaned sequence: {clean_seq}")
        
        # Validate the sequence
        is_valid, chain_obj, validation_results = validate_sequence(clean_seq)
        
        # Format results for output
        formatted_results = format_validation_results(validation_results)
        
        # Prepare the data to be saved to JSON
        output_data = {
            'raw_sequence': raw_seq,
            'cleaned_sequence': clean_seq,
            'validation': formatted_results,
            # Store tensor data as lists
            # 'generated_sequence': [seq.tolist() if hasattr(seq, 'tolist') else seq for seq in generated_sequence]
        }
        
        # Save the output data to a JSON file
        output_file_path = os.path.join(args.output_dir, f"{args.chain}.json")
        with open(output_file_path, 'w') as json_file:
            json.dump(output_data, json_file, indent=2)
        logger.info(f"Output saved to {output_file_path}")
        
        # Print validation summary
        print(f"\nGenerated sequence for {args.chain}:")
        print(f"Sequence: {clean_seq}")
        print(f"Length: {formatted_results['length']} amino acids")
        print(f"Valid: {formatted_results['valid']}")
        if formatted_results['valid']:
            print(f"Valid with schemes: {', '.join(formatted_results['valid_schemes'])}")
        
    except Exception as e:
        logger.error(f"Error during generation or validation: {str(e)}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()