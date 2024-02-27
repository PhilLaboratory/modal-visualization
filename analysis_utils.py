import pandas as pd
from plotnine import *

# Correlations
# Get pairs of modal terms for comparision
def get_corr_pairs(dataframe):
  col_names = dataframe.columns.tolist()
  # keep only the modal judgment response columns
  col_names = [name for name in col_names if name.endswith('resp_sp') or name.endswith('resp_rf')]
  # get all possible correlation pairs
  corr_pairs = [(col1, col2) for i, col1 in enumerate(col_names) for col2 in col_names[i+1:]]
  # keep only the pairs with consistent speed condition
  corr_pairs = [pair for pair in corr_pairs if (pair[0].endswith('_sp') and pair[1].endswith('_sp')) or (pair[0].endswith('_rf') and pair[1].endswith('_rf'))]

  return corr_pairs

# compute correlations
def get_correlation(dataframe, corr_pairs):
    data = {'response': [], 'relation': [], 'condition3': []}
    
    for pair in corr_pairs:
        col1, col2 = pair
        # shorten labels; 'poss_resp_rf-could_resp_rf' -> 'poss-could'
        data['relation'].append(f"{col1.split('_')[0]}-{col2.split('_')[0]}")
        # compute correlation
        data['response'].append(dataframe[col1].corr(dataframe[col2]))
        # label speed conditions
        if "_rf" in col1:
          data['condition3'].append("reflective")
        else:
          data['condition3'].append("speeded")
    
    result = pd.DataFrame(data)    
    return result

# updated function that computes correlation for a specifed subset of the action items
def get_correlation_2(dataframe, corr_pairs, filter=None): #filter should be a condition in STRING format. e.g., dataframe['condition1']=='immoral'; dataframe['mRating_immoral'] < 2.5
    # filter action items
    if filter is not None:
      dataframe = dataframe.loc[eval(filter)]

    result = {'response': [], 'relation': [], 'condition3': []}
    
    for pair in corr_pairs:
        col1, col2 = pair
        # shorten labels; 'poss_resp_rf-could_resp_rf' -> 'poss-could'
        result['relation'].append(f"{col1.split('_')[0]}-{col2.split('_')[0]}")
        # compute correlation
        result['response'].append(dataframe[col1].corr(dataframe[col2]))
        # label speed conditions
        if "_rf" in col1:
          result['condition3'].append("reflective")
        else:
          result['condition3'].append("speeded")
    
    result = pd.DataFrame(result)
    return result

# line graph comparing different sets of action
def corr_plot_multi(dataframe, corr_pairs, filter=None):
  corr_df = pd.DataFrame()
  for f in filter:
    filtered_df = get_correlation_2(dataframe, corr_pairs, f)
    filtered_df['level'] = f
    corr_df = pd.concat([corr_df, filtered_df])
  
  corr_plot = ggplot(corr_df, aes(x='condition3', y='response', color='relation')) \
                    + geom_point() \
                    + geom_line(aes(group='relation')) \
                    + facet_grid('.~level') \
                    + theme_classic()
  return corr_plot