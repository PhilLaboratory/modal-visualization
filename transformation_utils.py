import pandas as pd
import numpy as np
from dfply import *
import glob

# Reading & Cleaning data
# read a folder of cvs files as pandas dfs and store in a dictionary. for this to work, the folder must only contain possibility rating data (i.e. no norming, etc.)
def read_csv_folder(folder_path):
  # Get a list of .csv file paths in the folder
  csv_files = glob.glob(folder_path + '/*.csv')
  
  dataframes = {} # dictionary to store the dfs with file names as the keys

  for file in csv_files:
    file_name = file.split('/')[-1].split('.')[0]
    dataframe = pd.read_csv(file)
    dataframes[file_name] = dataframe
  
  return dataframes


# standardize variable and column names (of MTurk and Prolific data)
def rename_vars(dataframe):
    if ('condition3' in dataframe.columns) and ('fast' in dataframe['condition3'].values):
        dataframe['condition3'] = dataframe['condition3'].replace(['fast'], 'speeded')
        dataframe['condition3'] = dataframe['condition3'].replace(['slow'], 'reflective')
    
    if 'RTs' in dataframe.columns:
        dataframe = dataframe.rename(columns={'RTs': 'RT'})

    if 'responses' in dataframe.columns:
        dataframe = dataframe.rename(columns={'responses': 'response'})

    if 'turkID' in dataframe.columns:
        dataframe = dataframe.rename(columns={'turkID': 'id'})
    
    return dataframe

# Transforming possibility judgment data
# function to select relevant columns and rows
def select_cols(dataframe):
    # convert responses to numerics
    #dataframe['response'] = dataframe['response'].replace(['f'], 1) # changes value of 'f' under column 'responses' to 1
    #dataframe['response'] = dataframe['response'].replace(['j'], 0)
    #dataframe['response'] = dataframe['response'].replace(['timeout'], 99)

    dataframe['response'] = np.where(dataframe['response'] == 'f', 1, np.where(dataframe['response'] == 'j', 0, 99))
    
    # select relevant columns and rows
    result = dataframe >> select(X.condition1, X.condition2, X.condition3, X.target, X.RT, X.response, X.trialNo,
                             X.id) \
             >> mask(X.condition1 != 'na', X.condition1 != 'break') \
             >> mask(X.response != 99) \
             >> mutate(trialNo=X.trialNo)

    result['trialNo'] = result['trialNo'].astype(int)

    result['response'] = result['response'].astype(float)

    return result

# filter responses based on participant mean rt; compute mean RT and response for each event item (TrialNo)
# exclude participants whose mean RT for the speeded condition is below 800ms and those whose mean RT for the reflective condition is below 1000ms
def filterfunc(dataframe):
    dataframe['trialNo'] = dataframe['trialNo'].astype(int)
    exclude_speeded = dataframe >> filter_by(X.condition3 == 'speeded', X.RT <=6000) \
              >> select(X.trialNo, X.response, X.id, X.condition3, X.RT) \
              >> group_by(X.id) \
              >> summarize(mean_RT_s=mean(X.RT)) \
              >> filter_by(X.mean_RT_s < 800)

    exclude_reflective = dataframe >> filter_by(X.condition3 == 'reflective', X.RT <= 6000) \
                 >> select(X.trialNo, X.response, X.id, X.condition3, X.RT) \
                 >> group_by(X.id) \
                 >> summarize(mean_RT_r=mean(X.RT)) \
                 >> filter_by(X.mean_RT_r < 1000)

    final_speeded = dataframe[~dataframe.id.isin(exclude_speeded.id)] \
                    >> filter_by(X.condition3 == 'speeded', X.RT > 500) \
                    >> select(X.id, X.trialNo, X.condition3, X.response, X.RT) \
                    >> group_by(X.trialNo) >> summarize(mean_resp_sp=mean(X.response), mean_RT_sp=mean(X.RT))

    final_reflective = dataframe[~dataframe.id.isin(exclude_reflective.id)] \
                       >> filter_by(X.condition3 == 'reflective', X.RT > 1500) \
                       >> select(X.trialNo, X.response, X.id, X.condition3, X.RT) \
                       >> group_by(X.trialNo) >> summarize(mean_resp_rf=mean(X.response), mean_RT_rf=mean(X.RT))

    final_merged = pd.merge(final_speeded, final_reflective,on='trialNo', how='left') >> arrange(X.trialNo, ascending=True)
    return final_merged

# to compute mean response and RTs for the dictionary of dfs
def get_response_rt(dataframes):
  judgments = ['poss', 'could', 'may', 'might', 'ought', 'should'] #add/change as needed 

  for key, value in dataframes.items():
    dataframes[key] = filterfunc(select_cols(rename_vars(value)))

    #rename variables for later
    for j in judgments:
      if j in key:
        dataframes[key] = dataframes[key].rename(columns=lambda col: col.replace('mean', j) if 'mean' in col else col)

  return dataframes


# Transforming norming data
# function to summarize norming data
#def norming_transformation(dataframe):
  result = dataframe >> mutate(judgment=dataframe.target.apply(
      lambda x: 1 if 'moral' in x else 2 if 'rational' in x else 3 if 'likely' in x else x)) \
  #>> group_by(X.trialNo, X.condition1, X.condition2, X.judgment) \
  #>> summarize(meanresponse = mean(X.response)) \
  #>> select(X.condition1, X.condition2, X.trialNo, X.judgment, X.meanresponse) \
  #>> spread(X.judgment, X.meanresponse)

  #result.columns = ['condition1', 'condition2', 'trialNo', 'mRating_moral', 'mRating_rational', 'mRating_likely']
  #result['trialNo'] = result['trialNo'].astype(int)

  #return result

# a more automated version (6.27 update):
def norming_transformation_2(dataframe, values):

    dataframe = dataframe.dropna(subset=['target'])

    # label judgment type for each response
    for value in values:
      dataframe[value] = dataframe.target.str.contains(value).astype(int)
    dataframe['judgment'] = dataframe[values].idxmax(axis=1)
    dataframe['judgment'] = 'mRating_' + dataframe['judgment']

    # discard 'not applicable' responses
    dataframe['response'] = dataframe['response'].astype(int)
    dataframe = dataframe[dataframe['response'] != 6]


    result = dataframe >> group_by(X.trialNo, X.judgment) \
        >> summarize(meanresponse=mean(X.response)) \
        >> select(X.trialNo, X.judgment, X.meanresponse) \
        >> spread(X.judgment, X.meanresponse)

    result['trialNo'] = result['trialNo'].astype(int)

    # standardize column names and values
    if 'mRating_good of an idea' in result.columns: # for dataset 4+
      result = result.rename(columns={'mRating_good of an idea': 'mRating_goodness'})

    if 'mRating_morally wrong' in result.columns: # for dataset 1
      result = result.rename(columns={'mRating_morally wrong': 'mRating_immoral'})
      result['mRating_immoral'] = 6 - result['mRating_immoral']

    if 'mRating_likely' in result.columns: # for dataset 1
      result = result.rename(columns={'mRating_likely': 'mRating_improbable'})

    if 'mRating_irrational would' in result.columns: # for dataset 1
      result = result.rename(columns={'mRating_irrational would': 'mRating_irrational'})
      result['mRating_irrational'] = 6 - result['mRating_irrational']

    if 'mRating_irrational is' in result.columns: # for dataset 3
      result = result.rename(columns={'mRating_irrational is': 'mRating_irrational'})

    return result

def get_norming(path, all_judgments):

  all_judgments = all_judgments
  data = pd.read_csv(path)
  judgments = []

  for item in all_judgments:
    if data['target'].str.contains(item).any():
      judgments.append(item)

  result = norming_transformation_2(rename_vars(data), judgments)

  return result


# Get event list (updated on 2/27/24)
def get_event_list(dataframe):
  result = dataframe[['trialNo', 'target','condition1', 'condition2']].drop_duplicates(subset=['trialNo']).dropna().sort_values('trialNo')
  result['trialNo'] = result['trialNo'].astype(str)
  result = result[~result['trialNo'].str.contains('na')]
  result['trialNo'] = result['trialNo'].astype(float).astype(int)

  result['condition2'] = result['condition2'].str.extract(r'(\d+)', expand=False).astype(int) #temporarily convert scenario number into integers for convenience

  return result


# Combining data for one study
def joinfunc(main, data):
    result = pd.merge(main, data, on='trialNo', how='outer')
    return result

def joinfunc_multi(main, list):
    result = main
    for x in list:
      result = joinfunc(result, x)
    return result


# Combing data from multiple studies
# when needed, df2's trialNo and scenNo (condition2) will be adjusted to follow df1
def adjust_label(df1, df2):
  #adjust trialNo
  min_trialNo_df2 = df2['trialNo'].min()
  max_trialNo_df1 = df1['trialNo'].max()
  
  if min_trialNo_df2 <= max_trialNo_df1:
    adjust = max_trialNo_df1 + 1 - min_trialNo_df2
    df2['trialNo'] += adjust
  
  #adjust scenario number (condition2)
  min_scenNo_df2 = df2['condition2'].min()
  max_scenNo_df1 = df1['condition2'].max()

  if min_scenNo_df2 <= max_scenNo_df1:
    adjust2 = max_scenNo_df1 + 1 - min_scenNo_df2
    df2['condition2'] += adjust2

  return df1, df2

#append data from new study to exising ones
def append_study(df_old, df_new):
  #adjust trial and scen number if needed
  df_old, df_new = adjust_label(df_old, df_new)

  merged_df = pd.concat([df_old, df_new], ignore_index=True, sort=False)
  merged_df.fillna(value=np.nan, inplace=True)

  return merged_df
