import pandas as pd
import numpy as np
from dfply import *
import glob

from transformation_utils import *

import os

path_list = ['data/dataset1',
             'data/dataset2',
             'data/dataset3']

output_path = 'combinedData.csv'

combined_df = pd.DataFrame()


for path in path_list:

    # norming data
    norming_df = pd.DataFrame()
    norming_path = path + '/norming'
    
    if len(os.listdir(norming_path)) == 0:
       print('There is no norming data in ' + path)  
    else:
       norming_path = glob.glob(norming_path + '/*.csv')
       judgments = ['moral', 'rational', 'likely']            ## to be automated
       norming_df = get_norming(norming_path[0], judgments)


    # modal judgment data
    modal_path = path + '/modal_judgment'

    if len(os.listdir(modal_path)) == 0:
        print('There is no modal judgment data in ' + path)
    else:
        # read modal data as dictionary
        modal_data = read_csv_folder(modal_path)
    
        # get event list
        df = next(iter(modal_data.values()))
        event_list = get_event_list(df)
    
        # get modal judgment and rt
        response_rt = get_response_rt(modal_data)

    # combine data within study
    if len(norming_df)==0:
        main = event_list
    else:
        main = pd.merge(event_list, norming_df, on='trialNo', how='left')
  
    main = joinfunc_multi(main, list(response_rt.values())) #add response and rt
    

    main['trialNo'] = main['trialNo'].astype(int)
    main['condition2'] = main['condition2'].astype(int)

    
    """ #sanity check
    print("finish transforming current dataset" + path)
    print(main.shape) """

    # combine multiple studies
    if len(combined_df) == 0:
        combined_df = main
    else:
        combined_df, main = adjust_label(combined_df, main)
        combined_df = append_study(combined_df, main)

combined_df['trialNo'] = combined_df['trialNo'].astype(int)
combined_df['condition2'] = combined_df['condition2'].astype(int)
combined_df = combined_df.sort_values(by=['condition2', 'trialNo'])

#export combined data as csv
combined_df.to_csv(output_path, index=False)