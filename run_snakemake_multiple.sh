#!/bin/bash

# Configuration
TOTAL_RUNS_NEEDED=10
SUCCESSFUL_RUNS=0
MAX_ATTEMPTS=20  # Safety limit to prevent infinite loops
ATTEMPT=0

# Log file for tracking
LOG_FILE="snakemake_runs.log"
echo "Starting multiple Snakemake runs at $(date)" > $LOG_FILE

# Function to run Snakemake and handle result
run_snakemake() {
    echo "[$(date)] Attempt $ATTEMPT: Starting Snakemake run" | tee -a $LOG_FILE
    
    # Run your Snakemake command
    snakemake -s Snakefile --cores 1
    
    # Check if Snakemake was successful
    if [ $? -eq 0 ]; then
        SUCCESSFUL_RUNS=$((SUCCESSFUL_RUNS+1))
        echo "[$(date)] Success! Run $SUCCESSFUL_RUNS of $TOTAL_RUNS_NEEDED completed" | tee -a $LOG_FILE
        return 0
    else
        echo "[$(date)] Failed run. Cleaning up and will retry." | tee -a $LOG_FILE
        
        # Clean up the .current_experiment_name file
        if [ -f .current_experiment_name ]; then
            rm .current_experiment_name
            echo "[$(date)] Removed .current_experiment_name file" | tee -a $LOG_FILE
        else
            echo "[$(date)] Warning: .current_experiment_name file not found" | tee -a $LOG_FILE
        fi
        
        return 1
    fi
}

# Main loop to achieve 10 successful runs
while [ $SUCCESSFUL_RUNS -lt $TOTAL_RUNS_NEEDED ] && [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT+1))
    
    # Make sure .current_experiment_name is removed before starting
    if [ -f .current_experiment_name ]; then
        rm .current_experiment_name
        echo "[$(date)] Removed existing .current_experiment_name before starting" | tee -a $LOG_FILE
    fi
    
    # Run Snakemake
    run_snakemake
    
    # Optional: Add a short delay between runs
    sleep 2
done

# Final report
if [ $SUCCESSFUL_RUNS -eq $TOTAL_RUNS_NEEDED ]; then
    echo "[$(date)] All $TOTAL_RUNS_NEEDED successful runs completed in $ATTEMPT attempts!" | tee -a $LOG_FILE
else
    echo "[$(date)] Only achieved $SUCCESSFUL_RUNS successful runs after $MAX_ATTEMPTS attempts" | tee -a $LOG_FILE
    echo "[$(date)] Please check your Snakemake file for persistent issues" | tee -a $LOG_FILE
    exit 1
fi

exit 0