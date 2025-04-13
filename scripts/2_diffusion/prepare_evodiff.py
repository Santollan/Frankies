import subprocess
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--path", help="The file path of the Chain")
parser.add_argument("--h_chain", help="The file name of the L Chain")
parser.add_argument("--l_chain", help="The file name of the H Chain")
parser.add_argument("--output_config", help="Output directory for the results")

args = parser.parse_args()

# Properly join path and filename using os.path.join to ensure cross-platform compatibility
h_file_path = os.path.join(args.path, args.h_chain)
l_file_path = os.path.join(args.path, args.l_chain)
print("Full Heavy chain file path:", h_file_path)
print("Full Light chain file path:", l_file_path)


def count_sequences_and_max_length(file_path):
    count = 0
    max_length = 0
    sequence = ""

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()  # Remove any leading/trailing whitespace
            
            if line.startswith(">"):  # This is a header line
                # If sequence is not empty, finalize the last sequence
                if sequence:
                    max_length = max(max_length, len(sequence))
                    count += 1  # Increment sequence count
                    sequence = ""  # Reset for the next sequence
            else:
                if line:  # Only add to sequence if the line is not empty
                    sequence += line  # Add to current sequence

        # Handle the last sequence after the loop (in case the file ends with a sequence)
        if sequence:
            max_length = max(max_length, len(sequence))
            count += 1

    return count, max_length

# Function to create a config file

def create_config_file( h_file_path,l_chain, h_chain_data, l_chain_data):

    config_file_path = os.path.join(args.output_config)

    with open(config_file_path, 'w') as config_file:
        config_file.write(f"h_chain:\n")
        config_file.write(f" Number of sequences: {h_chain_data[0]}\n")
        config_file.write(f" Maximum sequence length: {h_chain_data[1]}\n")
        config_file.write(f"\n")
        config_file.write(f"l_chain:\n")
        config_file.write(f" Number of sequences: {l_chain_data[0]}\n")
        config_file.write(f" Maximum sequence length: {l_chain_data[1]}\n")
    return config_file_path

# Process the heavy chain file
h_num_sequences, h_max_length = count_sequences_and_max_length(h_file_path)
print(f"Number of sequences in heavy chain: {h_num_sequences}")
print(f"Maximum sequence length in heavy chain: {h_max_length}")

# Process the light chain file
l_num_sequences, l_max_length = count_sequences_and_max_length(l_file_path)
print(f"Number of sequences in light chain: {l_num_sequences}")
print(f"Maximum sequence length in light chain: {l_max_length}")


# Create the config file
config_file_path = create_config_file(
    h_file_path, l_file_path, 
    (h_num_sequences, h_max_length), 
    (l_num_sequences, l_max_length)
    )

print(f"Config file created at: {config_file_path}")
