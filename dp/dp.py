import numpy as np
import pandas as pd
import lapnoise as lap

def add_noise(filepath):
    f = open(filepath, 'r')
    lines = f.readlines()

    date = []
    raw_data = []
    empty_data= []
    for line in lines[1:]:
        item = line.split(",")
        date.append(item[0])
        try:
            raw_data.append(float(item[1].strip()))
        except ValueError:
            raw_data.append(0)
            empty_data.append(item[0])


    noised_data = [raw_data[i]+lap.laprnd(0,0.014) for i in range(0,len(raw_data))]

    dp_df = pd.DataFrame(data=noised_data, index=date)
    print(dp_df)

    return dp_df


add_noise('fridge.csv')
