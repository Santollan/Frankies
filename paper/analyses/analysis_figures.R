library(dplyr)
library(readxl)
library(ggplot2)
library(ggpubr)

## Figure Generation

## Load in data
data <- read_excel("antibody_metrics.xlsx") %>% 
  mutate(antibody_type = "diffused")


## Create Boxplots of metrics by Fv type
# plot_comparisons <- combn(c("reference", "diffused"), 2, simplify = FALSE)
# pymol_palette <- c("#4D4DFF","#1A9999")

### Stability - Total Energy
stb_boxplot <- ggboxplot(data,
                         x = "antibody_type",
                         y = "foldx_solubility_total_energy_kcalpermol",
                         xlab = "Diffused",
                         ylab = "Total Energy (kcal/mol)",
                         color = "#1A9999",
                         add = "dotplot") + 
  theme(axis.title.y=element_blank(),
        axis.text.y=element_blank(),
        axis.line.y=element_blank(),
        axis.ticks.y=element_blank(),
        legend.title=element_blank()) +
  coord_flip()

### Stability - Polar Solvation
sps_boxplot <- ggboxplot(data,
                         x = "antibody_type",
                         y = "foldx_solubility_solvation_polar",
                         xlab = "Diffused",
                         ylab = "Polar Solvation (kcal/mol)",
                         color = "#1A9999",
                         add = "dotplot") + 
  theme(axis.title.y=element_blank(),
        axis.text.y=element_blank(),
        axis.line.y=element_blank(),
        axis.ticks.y=element_blank(),
        legend.title=element_blank()) +
  coord_flip()

### Stability - Hydrophobic Solvation
shs_boxplot <- ggboxplot(data,
                         x = "antibody_type",
                         y = "foldx_solubility_solvation_hydrophobic",
                         xlab = "Diffused",
                         ylab = "Hydrophobic Solvation (kcal/mol)",
                         color = "#1A9999",
                         add = "dotplot") + 
  theme(axis.title.y=element_blank(),
        axis.text.y=element_blank(),
        axis.line.y=element_blank(),
        axis.ticks.y=element_blank(),
        legend.title=element_blank()) +
  coord_flip()



stability_boxplot_figure <- ggarrange(stb_boxplot,
                                      sps_boxplot,
                                      shs_boxplot,
                                      labels = c("A", "B", "C"),
                                      ncol = 1, nrow = 3,
                                      # ncol = 1, nrow = 5,
                                      common.legend = TRUE,
                                      legend = "bottom")

stability_boxplot_figure



## Humanness Density Plot
  
ggplot(data, aes(x=x) ) +
  # Top
  geom_density(aes(x = humatch_human_likeness_heavy_p, y = ..density..), fill="#1A9999" ) +
  geom_label( aes(x=0.5, y=0.1, label="Heavy Chains"), color="#1A9999") +
  # Bottom
  geom_density( aes(x = humatch_human_likeness_light_p, y = -..density..), fill= "#69b3a2") +
  geom_label( aes(x=0.5, y=-0.1, label="Light Chains"), color="#69b3a2") +
  theme_minimal() +
  scale_y_continuous(labels = scales::percent, limits = c(-1, 1)) +
  scale_x_continuous(labels = scales::percent, limits = c(0, 1)) +
  # xlim(0,1) +
  ylab("Density") +
  xlab("Predicted Human Likeness")


## pLDDT
library(ggExtra)

plddt_scatter <- ggplot(data, aes(x=mean_plddt, y=median_plddt)) +
  geom_point() +
  geom_smooth(method = "lm", se = FALSE, color = "#1A9999") +
  labs(x = "Mean pLDDT", y = "Median pLDDT") +
  theme_minimal() +
  theme(legend.position = "none") +
  # ggtitle("Mean vs Median pLDDT") +
  stat_cor(method = "pearson", label.x = 0.5, label.y = 0.5) +
  xlim(0.5, 1) + ylim(0.5, 1)

  
ggMarginal(plddt_scatter, type="boxplot", fill = "#1A9999",)
