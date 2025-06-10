#!/usr/bin/env python3
"""
FoldX Solubility Results Visualization Script
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import glob
import re

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def parse_foldx_stability_results(results_dir):
    """Parse all FoldX Stability output files"""
    results_path = Path(results_dir)
    stability_data = []
    
    # Find all analysis directories
    analysis_dirs = [d for d in results_path.iterdir() if d.is_dir() and d.name.endswith('_analysis')]
    
    for analysis_dir in analysis_dirs:
        experiment_name = analysis_dir.name.replace('_analysis', '')
        
        # Look for Stability output files
        stability_files = list(analysis_dir.glob("*_0_ST.fxout"))
        
        if stability_files:
            try:
                # Read the stability file
                with open(stability_files[0], 'r') as f:
                    lines = f.readlines()
                    
                for line in lines:
                    if line.strip() and not line.startswith('#') and '\t' in line:
                        parts = line.strip().split('\t')
                        if len(parts) >= 2:
                            try:
                                total_energy = float(parts[1])
                                stability_data.append({
                                    'experiment_name': experiment_name,
                                    'total_energy': total_energy,
                                    'pdb_file': parts[0] if len(parts) > 0 else 'unknown'
                                })
                                break
                            except ValueError:
                                continue
            except Exception as e:
                print(f"Error parsing {stability_files[0]}: {e}")
    
    return pd.DataFrame(stability_data)

def parse_foldx_analysecomplex_results(results_dir):
    """Parse all FoldX AnalyseComplex output files"""
    results_path = Path(results_dir)
    complex_data = []
    
    analysis_dirs = [d for d in results_path.iterdir() if d.is_dir() and d.name.endswith('_analysis')]
    
    for analysis_dir in analysis_dirs:
        experiment_name = analysis_dir.name.replace('_analysis', '')
        
        # Look for AnalyseComplex output files
        ac_files = list(analysis_dir.glob("*_AC.fxout"))
        
        if ac_files:
            try:
                with open(ac_files[0], 'r') as f:
                    lines = f.readlines()
                    
                # Parse the AC file for relevant metrics
                for line in lines:
                    if 'Total' in line and 'Energy' in line:
                        # This will need adjustment based on actual FoldX AC output format
                        parts = line.strip().split('\t')
                        # Add parsing logic here based on your AC file structure
                        pass
                        
                # For now, just record that AC analysis was done
                complex_data.append({
                    'experiment_name': experiment_name,
                    'ac_completed': True
                })
                        
            except Exception as e:
                print(f"Error parsing {ac_files[0]}: {e}")
    
    return pd.DataFrame(complex_data)

def parse_foldx_sequence_detail_results(results_dir):
    """Parse all FoldX SequenceDetail output files"""
    results_path = Path(results_dir)
    sequence_data = []
    
    analysis_dirs = [d for d in results_path.iterdir() if d.is_dir() and d.name.endswith('_analysis')]
    
    for analysis_dir in analysis_dirs:
        experiment_name = analysis_dir.name.replace('_analysis', '')
        
        # Look for SequenceDetail output files
        sd_files = list(analysis_dir.glob("*_SD.fxout"))
        
        if sd_files:
            try:
                df_sd = pd.read_csv(sd_files[0], sep='\t')
                
                # Calculate summary statistics
                total_residues = len(df_sd)
                mean_total_energy = df_sd.get('Total Energy', pd.Series()).mean()
                
                sequence_data.append({
                    'experiment_name': experiment_name,
                    'total_residues': total_residues,
                    'mean_residue_energy': mean_total_energy,
                    'sd_completed': True
                })
                        
            except Exception as e:
                print(f"Error parsing {sd_files[0]}: {e}")
    
    return pd.DataFrame(sequence_data)

def create_stability_overview_plot(stability_df, output_dir):
    """Create overview plots for stability analysis"""
    if stability_df.empty:
        print("No stability data found for plotting")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('FoldX Stability Analysis Overview', fontsize=16, fontweight='bold')
    
    # 1. Total Energy Distribution
    axes[0,0].hist(stability_df['total_energy'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
    axes[0,0].set_xlabel('Total Energy (kcal/mol)')
    axes[0,0].set_ylabel('Frequency')
    axes[0,0].set_title('Distribution of Total Energy')
    axes[0,0].axvline(stability_df['total_energy'].mean(), color='red', linestyle='--', 
                     label=f'Mean: {stability_df["total_energy"].mean():.2f}')
    axes[0,0].legend()
    
    # 2. Energy by Experiment (top 20 most stable)
    top_stable = stability_df.nsmallest(20, 'total_energy')
    axes[0,1].barh(range(len(top_stable)), top_stable['total_energy'], color='lightgreen')
    axes[0,1].set_yticks(range(len(top_stable)))
    axes[0,1].set_yticklabels(top_stable['experiment_name'], fontsize=8)
    axes[0,1].set_xlabel('Total Energy (kcal/mol)')
    axes[0,1].set_title('Top 20 Most Stable Structures')
    
    # 3. Energy by Experiment (top 20 least stable)
    least_stable = stability_df.nlargest(20, 'total_energy')
    axes[1,0].barh(range(len(least_stable)), least_stable['total_energy'], color='lightcoral')
    axes[1,0].set_yticks(range(len(least_stable)))
    axes[1,0].set_yticklabels(least_stable['experiment_name'], fontsize=8)
    axes[1,0].set_xlabel('Total Energy (kcal/mol)')
    axes[1,0].set_title('Top 20 Least Stable Structures')
    
    # 4. Box plot of energies
    axes[1,1].boxplot(stability_df['total_energy'])
    axes[1,1].set_ylabel('Total Energy (kcal/mol)')
    axes[1,1].set_title('Energy Distribution Statistics')
    axes[1,1].set_xticklabels(['All Experiments'])
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/stability_overview.png", dpi=300, bbox_inches='tight')
    plt.show()

def create_solubility_ranking_plot(stability_df, output_dir):
    """Create a ranking plot for solubility assessment"""
    if stability_df.empty:
        return
    
    # Sort by total energy (lower is more stable/soluble)
    sorted_df = stability_df.sort_values('total_energy')
    
    # Create color map based on energy quartiles
    q1 = sorted_df['total_energy'].quantile(0.25)
    q3 = sorted_df['total_energy'].quantile(0.75)
    
    colors = ['green' if x <= q1 else 'orange' if x <= q3 else 'red' 
              for x in sorted_df['total_energy']]
    
    plt.figure(figsize=(16, 10))
    bars = plt.barh(range(len(sorted_df)), sorted_df['total_energy'], color=colors, alpha=0.7)
    
    plt.yticks(range(len(sorted_df)), sorted_df['experiment_name'], fontsize=8)
    plt.xlabel('Total Energy (kcal/mol)', fontsize=12)
    plt.title('Solubility Ranking: All Experiments\n(Lower energy = More stable/soluble)', 
              fontsize=14, fontweight='bold')
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='green', alpha=0.7, label='Most Stable (Q1)'),
                      Patch(facecolor='orange', alpha=0.7, label='Moderate (Q2-Q3)'),
                      Patch(facecolor='red', alpha=0.7, label='Least Stable (Q4)')]
    plt.legend(handles=legend_elements, loc='lower right')
    
    # Add grid for better readability
    plt.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/solubility_ranking.png", dpi=300, bbox_inches='tight')
    plt.show()

def create_summary_statistics_table(stability_df, output_dir):
    """Create and save summary statistics"""
    if stability_df.empty:
        return
    
    # Calculate summary statistics
    stats = {
        'Total Experiments': len(stability_df),
        'Mean Energy (kcal/mol)': stability_df['total_energy'].mean(),
        'Std Energy (kcal/mol)': stability_df['total_energy'].std(),
        'Min Energy (kcal/mol)': stability_df['total_energy'].min(),
        'Max Energy (kcal/mol)': stability_df['total_energy'].max(),
        'Q1 Energy (kcal/mol)': stability_df['total_energy'].quantile(0.25),
        'Median Energy (kcal/mol)': stability_df['total_energy'].median(),
        'Q3 Energy (kcal/mol)': stability_df['total_energy'].quantile(0.75),
    }
    
    # Find best and worst performers
    best_experiment = stability_df.loc[stability_df['total_energy'].idxmin()]
    worst_experiment = stability_df.loc[stability_df['total_energy'].idxmax()]
    
    print("\n" + "="*60)
    print("FOLDX SOLUBILITY ANALYSIS SUMMARY")
    print("="*60)
    
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key:<30}: {value:>8.2f}")
        else:
            print(f"{key:<30}: {value:>8}")
    
    print(f"\nBest (Most Stable):")
    print(f"  Experiment: {best_experiment['experiment_name']}")
    print(f"  Energy: {best_experiment['total_energy']:.2f} kcal/mol")
    
    print(f"\nWorst (Least Stable):")
    print(f"  Experiment: {worst_experiment['experiment_name']}")
    print(f"  Energy: {worst_experiment['total_energy']:.2f} kcal/mol")
    
    # Save detailed results
    detailed_results = stability_df.sort_values('total_energy')
    detailed_results['stability_rank'] = range(1, len(detailed_results) + 1)
    detailed_results['stability_quartile'] = pd.qcut(detailed_results['total_energy'], 
                                                   q=4, labels=['Q1 (Best)', 'Q2', 'Q3', 'Q4 (Worst)'])
    
    detailed_results.to_csv(f"{output_dir}/detailed_solubility_results.csv", index=False)
    print(f"\nDetailed results saved to: {output_dir}/detailed_solubility_results.csv")

def create_interactive_analysis_report(results_dir, output_dir):
    """Create an interactive HTML report"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>FoldX Solubility Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; }}
            .summary {{ background-color: #ecf0f1; padding: 20px; border-radius: 5px; }}
            .highlight {{ background-color: #f39c12; color: white; padding: 5px; border-radius: 3px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #3498db; color: white; }}
        </style>
    </head>
    <body>
        <h1>FoldX Solubility Analysis Report</h1>
        
        <div class="summary">
            <h2>Analysis Overview</h2>
            <p>This report contains the results of FoldX stability analysis for protein solubility assessment.</p>
            <p><strong>Results Directory:</strong> {results_dir}</p>
            <p><strong>Generated:</strong> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <h2>Key Findings</h2>
        <ul>
            <li>Total experiments analyzed: <span class="highlight">[TO_BE_FILLED]</span></li>
            <li>Most stable structure: <span class="highlight">[TO_BE_FILLED]</span></li>
            <li>Average stability: <span class="highlight">[TO_BE_FILLED]</span> kcal/mol</li>
        </ul>
        
        <h2>Generated Visualizations</h2>
        <ul>
            <li><a href="stability_overview.png">Stability Overview Plots</a></li>
            <li><a href="solubility_ranking.png">Solubility Ranking Chart</a></li>
            <li><a href="detailed_solubility_results.csv">Detailed Results (CSV)</a></li>
        </ul>
        
        <h2>Interpretation Guide</h2>
        <ul>
            <li><strong>Lower total energy</strong> indicates more stable and potentially more soluble proteins</li>
            <li><strong>Q1 structures</strong> are in the top 25% for stability</li>
            <li><strong>Q4 structures</strong> may need optimization for better solubility</li>
        </ul>
    </body>
    </html>
    """
    
    with open(f"{output_dir}/analysis_report.html", 'w') as f:
        f.write(html_content)
    
    print(f"Interactive report saved to: {output_dir}/analysis_report.html")

def main():
    # Configuration
    results_dir = "foldx_results"
    output_dir = "foldx_visualizations"
    
    # Create output directory for visualizations
    Path(output_dir).mkdir(exist_ok=True)
    
    print("Parsing FoldX results...")
    
    # Parse different types of FoldX outputs
    stability_df = parse_foldx_stability_results(results_dir)
    complex_df = parse_foldx_analysecomplex_results(results_dir)
    sequence_df = parse_foldx_sequence_detail_results(results_dir)
    
    print(f"Found stability data for {len(stability_df)} experiments")
    print(f"Found complex analysis data for {len(complex_df)} experiments")
    print(f"Found sequence detail data for {len(sequence_df)} experiments")
    
    if not stability_df.empty:
        print("\nCreating visualizations...")
        
        # Create main visualizations
        create_stability_overview_plot(stability_df, output_dir)
        create_solubility_ranking_plot(stability_df, output_dir)
        create_summary_statistics_table(stability_df, output_dir)
        
        # Create interactive report
        create_interactive_analysis_report(results_dir, output_dir)
        
        print(f"\nAll visualizations saved to: {output_dir}/")
        print("Open 'analysis_report.html' in your browser for an interactive overview!")
    else:
        print("No stability data found. Please check that FoldX analysis completed successfully.")

if __name__ == "__main__":
    main()