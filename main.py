# script for data analysis and visualization (in progress)
import pandas as pd
from analysis_utils import *
from plotnine import *

# compute correlation
data = pd.read_csv("combinedData.csv")

# get correlations between modal judgments for all action items
corr_pairs = get_corr_pairs(data)
correlation_full = get_correlation(data, corr_pairs)
correlation_full.to_csv('output/correlation_full.csv', index=False)

# get correlations for selected actions items
correlation_1 = get_correlation_2(data, corr_pairs, "data['mRating_immoral'] >3")

# visualize correlations
conditions_1 = ["data['mRating_immoral'] <= 3", "data['mRating_immoral'] > 3"]
corr_plot1 = corr_plot_multi(data, corr_pairs, filter=conditions_1)
print(corr_plot1)