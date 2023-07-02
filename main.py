# script for data analysis and visualization (in progress)
import pandas as pd
from analysis_utils import *
from plotnine import *

# compute correlation
data = pd.read_csv("combinedData.csv")

# get correlations between modal judgments
corr_pairs = get_corr_pairs(data)
correlation_full = get_correlation(data, corr_pairs)
correlation_full.to_csv('output/correlation_full.csv', index=False)

# visualize correlations
corrplot_full = ggplot(correlation_full, aes(x='condition3', y='response', color='relation')) \
    + geom_point()\
    + geom_line(aes(group='relation')) \
    + theme_classic()
ggsave(corrplot_full, 'output/corrplot_full.png')