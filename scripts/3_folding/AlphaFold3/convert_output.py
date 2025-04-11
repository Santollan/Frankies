#!/usr/bin/env python3
"""
AlphaFold3 Output Converter
Converts AlphaFold3 output .cif files to .pdb format
"""

import os
import sys
import argparse
from pathlib import Path

try:
    import gemmi
except ImportError:
    print("Error: This script requires the gemmi library.")
    print("Please install it with: pip install gemmi")
    sys.exit(1)

def convert_alphafold_cif_to_pdb(cif_path, output_path=None, preserve_metadata=True):
    """
    Convert an AlphaFold3 .cif file to .pdb format
    
    Args:
        cif_path (str): Path to the input AlphaFold3 .cif file
        output_path (str, optional): Path for the output .pdb file
        preserve_metadata (bool): Whether to preserve AlphaFold-specific metadata
        
    Returns:
        str: Path to the created .pdb file
    """
    # Validate input file
    if not os.path.exists(cif_path):
        raise FileNotFoundError(f"Input file not found: {cif_path}")
    
    # Create output path if not specified
    if output_path is None:
        output_path = os.path.splitext(cif_path)[0] + '.pdb'
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        # Read the input CIF file
        structure = gemmi.read_structure(cif_path)
        
        # Process AlphaFold-specific metadata
        if preserve_metadata:
            # Retain b-factor for confidence scores
            # Note: AlphaFold typically stores pLDDT scores in B-factor column
            pass
        
        # Write as PDB format
        structure.write_pdb(output_path)
        
        print(f"Conversion successful: {cif_path} -> {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        raise

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Convert AlphaFold3 .cif output files to .pdb format')
    parser.add_argument('input', help='Input AlphaFold3 .cif file')
    parser.add_argument('-o', '--output', help='Output .pdb file')
    parser.add_argument('--no-metadata', action='store_true', 
                       help='Do not preserve AlphaFold-specific metadata')
    
    args = parser.parse_args()
    
    try:
        convert_alphafold_cif_to_pdb(
            args.input, 
            args.output, 
            preserve_metadata=not args.no_metadata
        )
    except Exception as e:
        print(f"Conversion failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())