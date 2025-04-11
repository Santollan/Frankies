---
title: "Antibody-Antigen Docking Experiment Report"
author: "Automated Pipeline"
date: "`r format(Sys.time(), '%Y-%m-%d')`"
format: 
  html:
    theme: cosmo
    toc: true
    code-fold: true
    fig-width: 8
    fig-height: 6
    embed-resources: true
params:
  experiment_dir: ""
  experiment_name: ""
  capri_scores_file: ""
  best_model_file: ""
---

```{r setup, include=FALSE}
knitr::opts_chunk$set(echo = TRUE, warning = FALSE, message = FALSE)
library(tidyverse)
library(kableExtra)
library(ggplot2)
library(plotly)
library(bio3d)
```

# Experiment Summary

This report provides an analysis of the antibody-antigen docking experiment: **`r params$experiment_name`**

```{r experiment-info}
# Get experiment details
experiment_dir <- params$experiment_dir
experiment_name <- params$experiment_name
capri_scores_file <- params$capri_scores_file
best_model_file <- params$best_model_file

# Display experiment details
experiment_details <- data.frame(
  Parameter = c("Experiment Name", "Experiment Directory", "Date Generated"),
  Value = c(experiment_name, experiment_dir, format(Sys.time(), '%Y-%m-%d %H:%M:%S'))
)

kable(experiment_details, caption = "Experiment Details") %>%
  kable_styling(bootstrap_options = c("striped", "hover", "condensed", "responsive"))
```

# CAPRI Scoring Results

The CAPRI (Critical Assessment of PRedicted Interactions) scores for the generated models are analyzed below. The best model is selected based on the lowest Van der Waals (VDW) energy.

```{r capri-scores}
# Read CAPRI scores
capri_scores <- read_tsv(capri_scores_file)

# Display the top 10 models sorted by VDW score
top_models <- capri_scores %>%
  arrange(VDW) %>%
  head(10)

kable(top_models, caption = "Top 10 Models by VDW Score") %>%
  kable_styling(bootstrap_options = c("striped", "hover", "condensed", "responsive"))

# Find best model info
best_model <- capri_scores %>%
  arrange(VDW) %>%
  slice(1)

# Create summary table
best_model_summary <- data.frame(
  Metric = c("Model ID", "VDW Score", "Electrostatic Score", "BSA (Buried Surface Area)", "Total Score"),
  Value = c(best_model$Model, best_model$VDW, best_model$Elec, best_model$BSA, best_model$Total)
)

kable(best_model_summary, caption = "Best Model Details (Lowest VDW Score)") %>%
  kable_styling(bootstrap_options = c("striped", "hover", "condensed", "responsive"))
```

# Visualization of Scoring Metrics

```{r score-plots}
# Create scatter plot of VDW vs Elec
p1 <- ggplot(capri_scores, aes(x = VDW, y = Elec, color = BSA, text = Model)) +
  geom_point(alpha = 0.7) +
  geom_point(data = best_model, color = "red", size = 5, shape = 8) +
  scale_color_viridis_c() +
  labs(title = "VDW vs Electrostatic Energy",
       x = "VDW Energy",
       y = "Electrostatic Energy",
       color = "BSA") +
  theme_minimal()

# Convert to interactive plot
ggplotly(p1, tooltip = c("x", "y", "text", "color"))
```

```{r distribution-plots}
# Create distribution plots for each metric
p2 <- capri_scores %>%
  pivot_longer(cols = c("VDW", "Elec", "BSA", "Total"), 
               names_to = "Metric", values_to = "Value") %>%
  ggplot(aes(x = Value, fill = Metric)) +
  geom_histogram(alpha = 0.7, bins = 30) +
  facet_wrap(~Metric, scales = "free") +
  theme_minimal() +
  labs(title = "Distribution of Scoring Metrics Across All Models")

p2
```

```{r correlation-plot}
# Create correlation matrix of the metrics
corr_data <- capri_scores %>%
  select(VDW, Elec, BSA, Total) %>%
  cor()

corrplot::corrplot(corr_data, method = "color", 
                   type = "upper", order = "hclust", 
                   tl.col = "black", tl.srt = 45,
                   addCoef.col = "black")
```

# Best Model Structure

The best model (based on lowest VDW score) is:

- **Model ID**: `r best_model$Model`
- **VDW Score**: `r best_model$VDW`
- **BSA (Buried Surface Area)**: `r best_model$BSA`
- **Electrostatic Score**: `r best_model$Elec`
- **Total Score**: `r best_model$Total`

```{r model-structure, eval=file.exists(best_model_file)}
# Only try to load the PDB if the file exists
if(file.exists(best_model_file)) {
  # Load the PDB structure
  best_pdb <- read.pdb(best_model_file)
  
  # Display basic structure information
  pdb_info <- data.frame(
    Property = c("Chains", "Total Residues", "Total Atoms"),
    Value = c(length(unique(best_pdb$atom$chain)), 
              length(unique(paste0(best_pdb$atom$chain, best_pdb$atom$resno))),
              nrow(best_pdb$atom))
  )
  
  kable(pdb_info, caption = "Best Model Structure Information") %>%
    kable_styling(bootstrap_options = c("striped", "hover", "condensed", "responsive"))
  
  # If R has a 3D viewer available, we can show the PDB structure
  if(requireNamespace("r3dmol", quietly = TRUE)) {
    r3dmol::r3dmol() %>%
      r3dmol::m_add_model(data = best_pdb$atom, format = "pdb") %>%
      r3dmol::m_set_style(style = "cartoon") %>%
      r3dmol::m_zoom_to()
  } else {
    cat("3D viewer not available. Install the r3dmol package to view the structure.")
  }
} else {
  cat("Best model PDB file not found. Structure visualization is unavailable.")
}
```

# Multi-Run Comparison

If you have run multiple experiments, you can compare their results here.

```{r multi-run, eval=FALSE}
# This code should be customized based on how you want to compare multiple runs
# For example, you might have a CSV file that tracks the best scores across experiments

# Example code (not run by default):
# experiment_comparison <- read_csv("path/to/experiment_comparison.csv")
# 
# ggplot(experiment_comparison, aes(x = Experiment, y = BestVDW)) +
#   geom_bar(stat = "identity") +
#   theme_minimal() +
#   labs(title = "Comparison of Best VDW Scores Across Experiments",
#        x = "Experiment",
#        y = "Best VDW Score")
```

# Conclusions

This report summarizes the results of the antibody-antigen docking experiment. The best model, selected based on the lowest VDW energy, has been identified and exported. Further analysis and validation may be necessary to confirm the biological relevance of this model.

For further details, please refer to the raw data files in the experiment directory.
