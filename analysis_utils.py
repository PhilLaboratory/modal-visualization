import pandas as pd

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

