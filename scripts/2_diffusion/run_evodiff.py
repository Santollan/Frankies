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


def read_config(config_path):
    """
    Read the configuration file and parse the sequence parameters.
    
    Args:
        config_path: Path to the config file
        
    Returns:
        Dictionary with chain parameters
    """
    chain_params = {
        'h_chain': {'sequence_count': 0, 'max_sequence': 0},
        'l_chain': {'sequence_count': 0, 'max_sequence': 0}
    }
    
    current_chain = None
    
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a chain header
            if line.startswith('h_chain:'):
                current_chain = 'h_chain'
            elif line.startswith('l_chain:'):
                current_chain = 'l_chain'
            elif current_chain and 'number of sequences' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    try:
                        chain_params[current_chain]['sequence_count'] = int(parts[1].strip())
                    except ValueError:
                        logger.error(f"Invalid sequence count in config: {line}")
            elif current_chain and 'maximum sequence length' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    try:
                        chain_params[current_chain]['max_sequence'] = int(parts[1].strip())
                    except ValueError:
                        logger.error(f"Invalid max sequence length in config: {line}")

    
    return chain_params


def main():
    """Main function to run the script"""
    parser = argparse.ArgumentParser(description="Generate and validate antibody sequences")
    parser.add_argument("--config", type=str, default="evodiff_config.txt",
                       help="Path to the configuration file")
    parser.add_argument("--path", type=str, required=True,
                       help="The directory path containing the MSA file")
    parser.add_argument("--chain", type=str, required=True,
                       help="Chain type (h_chain or l_chain)")
    parser.add_argument("--output_dir", type=str, default="/workspace/evodiff/frankie/experiment/2_diffusion/evodiff/",
                       help="Directory to save output files")
    parser.add_argument("--device", type=str, default="cpu",
                       help="Device to use for generation (cpu or cuda:N)")
    parser.add_argument("--selection_type", type=str, default="MaxHamming",
                       choices=["random", "MaxHamming"],
                       help="MSA subsampling scheme"),
    # parser.add_argument("--path_to_msa", type=str, required=True,
    #                    help="Path to the MSA file")
    
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
    
    # Read configuration file
    config_path = "/workspace/evodiff/frankie/experiment/2_diffusion/evodiff/evo_config.txt"
    if not os.path.exists(config_path):
        logger.error(f"Config file not found at {config_path}")
        exit(1)
    
    chain_params = read_config(config_path)
    print(chain_params)
    # Validate specified chain type
    if args.chain not in ['h_chain', 'l_chain']:
        logger.error(f"Invalid chain type: {args.chain}. Must be 'h_chain' or 'l_chain'")
        exit(1)
    
    # Get parameters for the specified chain
    sequence_count = chain_params[args.chain]['sequence_count']
    max_sequence = chain_params[args.chain]['max_sequence']
    
    if sequence_count == 0 or max_sequence == 0:
        logger.error(f"Invalid parameters for {args.chain} in config file: sequence_count={sequence_count}, max_sequence={max_sequence}")
        exit(1)
    
    logger.info(f"Using parameters for {args.chain}: sequence_count={sequence_count}, max_sequence={max_sequence}")
    
    # Load the MSA file
    path_to_msa = os.path.join(args.path)
    print(path_to_msa)
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
    logger.info(f"Parameters: n_sequences={sequence_count}, seq_length={max_sequence}")
    
    try:
        tokenized_sample, generated_sequence = generate_query_oadm_msa_simple(
            path_to_msa, model, tokenizer, sequence_count, max_sequence,
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
        output_file = f"{args.chain.split('_')[0]}_chain.json"  # Convert e.g. "h_chain" to "h_chain.json"
        output_file_path = os.path.join(args.output_dir, output_file)
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