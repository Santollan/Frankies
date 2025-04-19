import os
import sys
import logging
import time
import re
import torch
import json
from datetime import datetime

# Setup logging
log_filename = f"evodiff_generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

# Import EvoDiff and abnumber modules
try:
    from evodiff.pretrained import MSA_OA_DM_MAXSUB
    from evodiff.generate_msa import generate_query_oadm_msa_simple
    from abnumber import Chain
    logging.info("Successfully imported all required modules")
except ImportError as e:
    logging.error(f"Error importing modules: {e}")
    sys.exit(1)

# Function to clean sequences
def clean_sequence(seq):
    """Clean the sequence by removing padding tokens and mapping non-standard amino acids."""
    # Remove padding tokens and any non-amino acid characters
    seq = re.sub(r'[!-]', '', seq)
    
    # Standard amino acids for filtering
    STANDARD_AA = set("ACDEFGHIKLMNPQRSTVWY")
    
    # Non-standard mapping dictionary
    NON_STANDARD_MAPPING = {
        'B': 'D',  # Aspartic acid or Asparagine -> Aspartic acid
        'Z': 'E',  # Glutamic acid or Glutamine -> Glutamic acid
        'X': 'A',  # Unknown -> Alanine (arbitrary choice)
        'U': 'C',  # Selenocysteine -> Cysteine
        'O': 'K',  # Pyrrolysine -> Lysine
        'J': 'L',  # Not standard -> Leucine (closest biochemical property)
        '*': '',   # Stop codon -> Remove
        '~': '',   # Non-standard -> Remove
        '.': '',   # Sometimes used as a gap -> Remove
    }
    
    # Map non-standard amino acids to standard ones
    cleaned_seq = ''
    for aa in seq:
        if aa in STANDARD_AA:
            cleaned_seq += aa
        elif aa in NON_STANDARD_MAPPING:
            cleaned_seq += NON_STANDARD_MAPPING[aa]
        else:
            # Log any uncovered non-standard amino acids and default to Alanine
            logging.warning(f"Encountered unknown amino acid code '{aa}', replacing with 'A'")
            cleaned_seq += 'A'
    
    return cleaned_seq

def validate_antibody_chain(seq, scheme='kabat'):
    """Validate if a sequence is a valid antibody chain using abnumber."""
    try:
        # Try to parse with abnumber
        chain = Chain(seq, scheme=scheme)
        
        # Check if CDRs were detected
        has_cdr1 = hasattr(chain, 'cdr1') and chain.cdr1
        has_cdr2 = hasattr(chain, 'cdr2') and chain.cdr2  
        has_cdr3 = hasattr(chain, 'cdr3') and chain.cdr3
        
        # If all CDRs were detected, it's likely a valid antibody chain
        if has_cdr1 and has_cdr2 and has_cdr3:
            return True, chain
        else:
            return False, None
    except Exception as e:
        logging.warning(f"Error validating sequence: {e}")
        return False, None

def generate_valid_sequence(path_to_msa, model, tokenizer, n_sequences, seq_length, 
                           max_attempts=20, scheme='kabat', device='cpu', selection_type='random'):
    """Generate a valid antibody sequence, trying up to max_attempts times."""
    
    device_id = 0 if device == 'cuda' else device
    
    for attempt in range(1, max_attempts + 1):
        logging.info(f"Attempt {attempt}/{max_attempts} to generate a valid sequence")
        
        try:
            # Generate a sequence using EvoDiff
            tokenized_sample, generated_sequence = generate_query_oadm_msa_simple(
                path_to_msa, model, tokenizer, 
                n_sequences=n_sequences, 
                seq_length=seq_length, 
                device=device_id,
                selection_type=selection_type
            )
            
            # Get the first sequence from the batch
            raw_seq = generated_sequence[0][0]
            logging.info(f"Generated raw sequence: {raw_seq}")
            
            # Clean the sequence
            cleaned_seq = clean_sequence(raw_seq)
            logging.info(f"Cleaned sequence: {cleaned_seq}")
            
            # Validate the sequence
            is_valid, chain_obj = validate_antibody_chain(cleaned_seq, scheme)
            
            if is_valid:
                logging.info(f"Valid antibody sequence found on attempt {attempt}!")
                logging.info(f"CDR1: {chain_obj.cdr1}")
                logging.info(f"CDR2: {chain_obj.cdr2}")
                logging.info(f"CDR3: {chain_obj.cdr3}")
                
                return {
                    "success": True,
                    "raw_sequence": raw_seq,
                    "cleaned_sequence": cleaned_seq,
                    "attempt": attempt,
                    "cdr1": chain_obj.cdr1,
                    "cdr2": chain_obj.cdr2,
                    "cdr3": chain_obj.cdr3
                }
            else:
                logging.warning(f"Generated sequence is not a valid antibody (attempt {attempt})")
        
        except Exception as e:
            logging.error(f"Error in generation attempt {attempt}: {e}")
    
    # If we've reached here, all attempts failed
    logging.error(f"Failed to generate a valid sequence after {max_attempts} attempts")
    return {
        "success": False,
        "attempts": max_attempts
    }

def main():
    # Configure CUDA if available
    cuda_available = torch.cuda.is_available()
    device = 'cuda' if cuda_available else 'cpu'
    logging.info(f"Using device: {device}")
    
    if device == 'cuda':
        torch.set_default_device('cuda:0')
    
    # Load the model
    logging.info("Loading EvoDiff model...")
    try:
        checkpoint = MSA_OA_DM_MAXSUB()
        model, collater, tokenizer, scheme = checkpoint
        logging.info("Model loaded successfully")
    except Exception as e:
        logging.error(f"Error loading model: {e}")
        sys.exit(1)
    
    # Set parameters
    path_to_msa = '/mnt/data/inputs/anti-HA_antibodies_Hchains_aligned.fasta'
    n_sequences = 14  # number of sequences in MSA to subsample
    seq_length = 150  # maximum sequence length to subsample
    selection_type = 'random'  # or 'MaxHamming'; MSA subsampling scheme
    max_attempts = 20  # maximum number of generation attempts
    
    # Generate a valid sequence
    start_time = time.time()
    result = generate_valid_sequence(
        path_to_msa, model, tokenizer, 
        n_sequences, seq_length, 
        max_attempts=max_attempts,
        scheme='kabat',  # abnumber numbering scheme
        device=device,
        selection_type=selection_type
    )
    end_time = time.time()
    
    # Log the results
    if result["success"]:
        logging.info(f"Successfully generated a valid antibody sequence in {result['attempt']} attempts")
        logging.info(f"Execution time: {end_time - start_time:.2f} seconds")
        
        # Save the result to a JSON file
        output_file = f"valid_sequence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        logging.info(f"Results saved to {output_file}")
    else:
        logging.error(f"Failed to generate a valid sequence after {result['attempts']} attempts")

if __name__ == "__main__":
    main()
