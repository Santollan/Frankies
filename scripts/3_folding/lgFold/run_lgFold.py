import json
from igfold import IgFoldRunner
from pyrosetta import init as init_pyrosetta

# Example usage
hchain_file = "/Users/nick/Documents/GitHub/Frankies/experiments/test/2_diffusion/Hchains_aligned.a3m.json"
lchain_file = "/Users/nick/Documents/GitHub/Frankies/experiments/test/2_diffusion/Lchains_aligned.a3m.json"

# Function to generate alphafold json
def generate_alphafold_json(hchain_file, lchain_file):
    # Load the Hchain and Lchain JSON files
    with open(hchain_file, 'r') as f:
        hchain_data = json.load(f)
    
    with open(lchain_file, 'r') as f:
        lchain_data = json.load(f)
    
    # Extract the generated sequences
    hchain_sequence = hchain_data['generated_sequence'][0][0].strip()
    lchain_sequence = lchain_data['generated_sequence'][0][0].strip()


    # Output the sequences for debugging
    print("Extracted H chain sequence:", hchain_sequence)
    print("Extracted L chain sequence:", lchain_sequence)
    # Ensure the sequences are correctly assigned before being used
    sequences = {
        "H": hchain_sequence,
        "L": lchain_sequence
    }
    
    # Output for debugging
    print("H chain sequence:", hchain_sequence)
    print("L chain sequence:", lchain_sequence)
    print("Sequences dictionary:", sequences)
    
    # Return the sequences dictionary
    return sequences

# Call the function and capture the sequences
sequences = generate_alphafold_json(hchain_file, lchain_file)
print(f"Attempting to parse the following sequence: {sequences}")

# Initialize PyRosetta
init_pyrosetta()

# Define the output PDB file
pred_pdb = "my_antibody.pdb" #"experiments/test/3_folding/lgFold/my_antibody.pdb"
#fasta_file = "my_antibody.fasta" #"experiments/test/3_folding/lgFold/my_antibody.fasta"
# Initialize IgFoldRunner and run folding
igfold = IgFoldRunner()
igfold.fold(
    pred_pdb, # Output PDB file
    #fasta_file=fasta_file, # Output FASTA file
    sequences=sequences, # Antibody sequences
    do_refine=True, # Refine the antibody structure with PyRosetta
    do_renum=True, # Renumber predicted antibody structure (Chothia)
)
