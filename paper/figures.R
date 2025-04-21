library(dplyr)
library(readxl)
library(ggplot2)
library(ggpubr)

## Figure Generation

## Load in data
data <- read_excel("experiments.xlsx", sheet = "HA1-docking") 


## Create Boxplots of metrics by Fv type
plot_comparisons <- combn(c("reference", "diffused"), 2, simplify = FALSE)
pymol_palette <- c("#4D4DFF","#1A9999")

### VDW Energy
vdw_boxplot <- ggboxplot(data,
                         x = "antibody_type",
                         y = "vdw_best",
                         xlab = "",
                         ylab = "Van der Waals Energy",
                         color = "antibody_type",
                         palette = pymol_palette,
                         add = "dotplot") + 
  theme(axis.title.x=element_blank(),
        axis.text.x=element_blank(),
        axis.ticks.x=element_blank(),
        legend.title=element_blank()) +
  stat_compare_means(method = "wilcox.test",
                     comparisons = plot_comparisons)

### Electrostatic Energy
ee_boxplot <- ggboxplot(data,
                        x = "antibody_type",
                        y = "elec_best",
                        xlab = "",
                        ylab = "Electrostatic Energy",
                        color = "antibody_type",
                        palette = pymol_palette,
                        add = "dotplot") + 
  theme(axis.title.x=element_blank(),
        axis.text.x=element_blank(),
        axis.ticks.x=element_blank(),
        legend.title=element_blank()) +
  stat_compare_means(method = "wilcox.test",
                     comparisons = plot_comparisons)


### Desolvation Energy
de_boxplot <- ggboxplot(data,
                        x = "antibody_type",
                        y = "haddock_Edesolv",
                        xlab = "",
                        ylab = "Desolvation Energy",
                        color = "antibody_type",
                        palette = pymol_palette,
                        add = "dotplot") + 
  theme(axis.title.x=element_blank(),
        axis.text.x=element_blank(),
        axis.ticks.x=element_blank(),
        legend.title=element_blank()) +
  stat_compare_means(method = "wilcox.test",
                     comparisons = plot_comparisons)


### Buried Surface Area
bsa_boxplot <- ggboxplot(data,
                         x = "antibody_type",
                         y = "bsa_best",
                         xlab = "",
                         ylab = "Buried Surface Area",
                         color = "antibody_type",
                         palette = pymol_palette,
                         add = "dotplot") + 
  theme(axis.title.x=element_blank(),
        axis.text.x=element_blank(),
        axis.ticks.x=element_blank(),
        legend.title=element_blank()) +
  stat_compare_means(method = "wilcox.test",
                     comparisons = plot_comparisons)


### Total Score
tot_boxplot <- ggboxplot(data,
                         x = "antibody_type",
                         y = "total_best",
                         xlab = "",
                         ylab = "Total Score",
                         color = "antibody_type",
                         palette = pymol_palette,
                         add = "dotplot") + 
  theme(axis.title.x=element_blank(),
        axis.text.x=element_blank(),
        axis.ticks.x=element_blank(),
        legend.title=element_blank()) +
  stat_compare_means(method = "wilcox.test",
                     comparisons = plot_comparisons)


### HADDOCK Score
had_boxplot <- ggboxplot(data,
                         x = "antibody_type",
                         y = "haddock_score_best",
                         xlab = "",
                         ylab = "HADDOCK Score",
                         color = "antibody_type",
                         palette = pymol_palette,
                         add = "dotplot") + 
  theme(axis.title.x=element_blank(),
        axis.text.x=element_blank(),
        axis.ticks.x=element_blank(),
        legend.title=element_blank()) +
  stat_compare_means(method = "wilcox.test",
                     comparisons = plot_comparisons)



boxplot_figure <- ggarrange(vdw_boxplot,
                            ee_boxplot,
                            # dre_boxplot,
                            bsa_boxplot,
                            tot_boxplot,
                            had_boxplot,
                            labels = c("A", "B", "C", "D", "E", "F"),
                            ncol = 2, nrow = 3,
                            # ncol = 1, nrow = 5,
                            common.legend = TRUE,
                            legend = "bottom")

boxplot_figure


### Export as PDF in 11" x 4.25"


## UMAP
library(umap)

umap_fit <- data %>%
  select(antibody_id,
         haddock_Evdw,
         haddock_Eelec,
         haddock_Edesolv,
         haddock_Eair,
         haddock_BSA,
         haddock_prodigy_deltaG_kcalpermol) %>%
  tibble::column_to_rownames("antibody_id") %>%
  scale() %>% 
  umap()


umap_df <- umap_fit$layout %>%
  as.data.frame()%>%
  rename(UMAP1="V1",
         UMAP2="V2") %>%
  tibble::rownames_to_column(var = "antibody_id") %>% 
  inner_join(data, by="antibody_id")


umap_df %>%
  ggplot(aes(
    x = UMAP1,
    y = UMAP2,
    color = antibody_sequence_source,
    shape = antibody_sequence_source)) +
  # geom_point(size=3, alpha=0.5) +
  geom_label(
    label=umap_df$antibody_id
  ) +
  theme_pubr() +
  theme(legend.position = "none")
