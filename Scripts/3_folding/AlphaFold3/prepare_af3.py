import json

def generate_alphafold_json(hchain_file, lchain_file, output_file):
    # Load the Hchain and Lchain JSON files
    with open(hchain_file, 'r') as f:
        hchain_data = json.load(f)
    
    with open(lchain_file, 'r') as f:
        lchain_data = json.load(f)
    
    # Extract the generated sequences
    hchain_sequence = hchain_data['generated_sequence'][0][0]
    lchain_sequence = lchain_data['generated_sequence'][0][0]

    # Create the structure for AlphaFold3 JSON
    alphafold_data = {
  "name": "Antibody",
  "modelSeeds": [
    1234
  ],
  "sequences": [
    {
      "protein": {
        "id": "H",
        "sequence": hchain_sequence.strip(),
      }
    },
    {
      "protein": {
        "id": "L",
        "sequence": lchain_sequence.strip(),
      }
    }
  ],
  "dialect": "alphafold3",
  "version": 1
}
    
    # Save the generated data into a new JSON file
    with open(output_file, 'w') as f:
        json.dump(alphafold_data, f, indent=4)
    
    print(f"Generated AlphaFold JSON saved to {output_file}")


# Example usage
hchain_file = "/Users/nick/Documents/GitHub/Frankies/experiments/test/2_diffusion/Hchains_aligned.a3m.json"
lchain_file = "/Users/nick/Documents/GitHub/Frankies/experiments/test/2_diffusion/Lchains_aligned.a3m.json"
output_file = "/Users/nick/Documents/GitHub/Frankies/experiments/test/3_folding/AlphaFold3/alphafold_input.json"

generate_alphafold_json(hchain_file, lchain_file, output_file)
