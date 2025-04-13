import subprocess
import argparse
import os
parser = argparse.ArgumentParser()

parser.add_argument("--path", help="The file path of the Chain")
parser.add_argument("--chain", help="The file name of the Chain")



args = parser.parse_args()

# Properly join path and filename using os.path.join to ensure cross-platform compatibility
file_path = os.path.join(args.path, args.chain)

print("Full file path:", file_path)


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

def run_evo_command(num_sequences, max_length):
    # Construct the bash command
    command = [
        "python3", "frankie/run_evodiff.py",
        "--sequence_count", str(num_sequences),
        "--max_sequence", str(max_length),
        "--path", args.path,
        "--chain", args.chain,
        "--device", 0 ,
        "--output_dir", "/workspace/evodiff/frankie/experiment/2_diffusion/",
    ]
    
    # Run the command
    subprocess.run(command)

# Replace with your .a3m file path
#file_path = '/home/bigboy/Desktop/test junk/evodiff/PD1_Hchains_aligned.a3m'  # Replace with your file path

# Get number of sequences and max sequence length
num_sequences, max_length = count_sequences_and_max_length(file_path)

# Print the results
print(f"Number of sequences: {num_sequences}")
print(f"Maximum sequence length: {max_length}")

# Run the evo.py script with the calculated values
run_evo_command(num_sequences, max_length)

