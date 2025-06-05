library(Biostrings)
library(readxl)
library(dplyr)
library(tidyr)
library(ggplot2)
library(gridExtra)

data <- read_xlsx("../experiments.xlsx") %>% 
  select(antibody_id, antibody_type, h_chain, l_chain)

reference_mabs <- data %>%
  filter(antibody_type == "reference") %>% 
  pull(antibody_id)

diffused_mabs <- data %>%
  filter(!antibody_type == "reference") %>% 
  pull(antibody_id)

comparisons <- expand.grid(reference_mabs, diffused_mabs) %>% 
  rename(all_of(c(reference = "Var1", diffused = "Var2")))

## Create blank dataframe
h_seq_identity <- matrix(
  nrow = length(diffused_mabs),
  ncol = length(reference_mabs),
  dimnames = list(diffused_mabs, reference_mabs)
)

l_seq_identity <- matrix(
  nrow = length(diffused_mabs),
  ncol = length(reference_mabs),
  dimnames = list(diffused_mabs, reference_mabs)
)

## Define identity function
get_identity <- function(seq1, seq2){
  seq1 <- AAString(seq1)
  seq2 <- AAString(seq2)
  alignment <- pairwiseAlignment(seq1, seq2, type = "global")
  identity <- pid(alignment, type = "PID2") / 100
  
  return(identity)
}

## Fill out the heavy matrix
for(j in 1:ncol(h_seq_identity)){
  for(i in 1:nrow(h_seq_identity)){
    diffused_name <- row.names(h_seq_identity)[i]
    reference_name <- colnames(h_seq_identity)[j]
    
    seq1 <- data %>% filter(antibody_id == diffused_name) %>% 
      pull(h_chain)
      
    seq2 <- data %>% filter(antibody_id == reference_name) %>% 
      pull(h_chain)
    
    paste0("Getting sequence identity for: ", diffused_name, " X ", reference_name)
    
    h_seq_identity[i,j] <- get_identity(seq1, seq2)
  }
}

h_seq_identity_df <- as.data.frame(h_seq_identity)

h_seq_identity_df_pvt <- h_seq_identity_df %>% 
  tibble::rownames_to_column("diffused") %>% 
  pivot_longer(!diffused, names_to = "reference", values_to = "identity") %>% 
  mutate(chain = "Heavy Chain")

## Fill out the light matrix
for(j in 1:ncol(l_seq_identity)){
  for(i in 1:nrow(l_seq_identity)){
    diffused_name <- row.names(l_seq_identity)[i]
    reference_name <- colnames(l_seq_identity)[j]
    
    seq1 <- data %>% filter(antibody_id == diffused_name) %>% 
      pull(l_chain)
    
    seq2 <- data %>% filter(antibody_id == reference_name) %>% 
      pull(l_chain)
    
    paste0("Getting sequence identity for: ", diffused_name, " X ", reference_name)
    
    l_seq_identity[i,j] <- get_identity(seq1, seq2)
  }
}

l_seq_identity_df <- as.data.frame(l_seq_identity)

l_seq_identity_df_pvt <- l_seq_identity_df %>% 
  tibble::rownames_to_column("diffused") %>% 
  pivot_longer(!diffused, names_to = "reference", values_to = "identity") %>% 
  mutate(chain = "Light Chain")

## Plots
# h_heatmap <- ggplot(h_seq_identity_df_pvt, aes(x = reference, y = diffused, fill = identity)) +
#   geom_tile() +
#   scale_fill_gradient(low = "blue", high = "red", limits=c(0,1)) +
#   labs(title = "Heavy Fv Chains", x = "Reference Antibodies", y = "Diffused Antibodies") +
#   theme_minimal() +
#   theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1), legend.position="none")
# 
# l_heatmap <- ggplot(l_seq_identity_df_pvt, aes(x = reference, y = diffused, fill = identity)) +
#   geom_tile() +
#   scale_fill_gradient(low = "blue", high = "red", limits=c(0,1)) +
#   labs(title = "Light Fv Chains", x = "Reference Antibodies", y = "Diffused Antibodies") +
#   theme_minimal() +
#   theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1))

## Heatmap
plot_heatmap <- ggplot(rbind(h_seq_identity_df_pvt, l_seq_identity_df_pvt),
       aes(x = reference, y = diffused, fill = identity)) +
  geom_tile() +
  scale_fill_gradient(
    low = "blue", high = "red",
    limits = c(0,1),
    name = "Identity",
    labels = scales::label_percent()) +
  labs(
    # title = "Fv Sequence Identity",
    x = "Reference Antibodies",
    y = "Diffused Antibodies") +
  # theme_minimal() +
  theme_classic() +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
  facet_grid(~chain)

## Boxplot
plot_boxplot <- ggplot(rbind(h_seq_identity_df_pvt, l_seq_identity_df_pvt),
       aes(x = identity, y = "")) +
  geom_violin(fill = "grey") +
  # geom_polygon(aes(group = 1)) +
  # geom_dotplot(binaxis='y', stackdir='center', dotsize=1)
  geom_boxplot(width=0.5) +
  scale_fill_gradient(
    low = "blue", high = "red",
    limits = c(0,1),
    name = "Identity",
    labels = scales::label_percent()) +
  labs(
    # title = "Fv Sequence Identity",
    x = "Identity",
    y = "Density"
    ) +
  scale_x_continuous(labels = scales::label_percent(), limits=c(0,1)) +
  # theme_minimal() +
  theme_classic() +
  # theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1))
  facet_grid(~chain)


ggpubr::ggarrange(
  ggpubr::ggarrange(
    NULL,
    plot_boxplot,
    ncol = 3,
    widths = c(0.5, 2, 0.5)
    ),
  plot_heatmap,
  nrow = 2, ncol = 1,
  heights = c(1, 2),
  align = "h",
  labels = c("A", "B")
)
