# L.Bongartz 15.03.2023
#
# This script is for preparing the input data as a single file, in which the snippets are seperated by sequences of 0V. The length of
# this sequence will become important when we want to make use of the memory funtionality
#
# Here is also where you can change the y-offset. This will important to make the device more sensitive.

import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Insert your parameters here
rate = 100 # Default rate of the input data is 100Hz
seconds_zeros = 0.2 # For how long (in s) 0V is applied between each data snippet
y_offset = 0 # Offset (in V)

# Where are the files located that you want to use as input?
path = r'C:\Users\lbongartz\Desktop\Reservoir Computing\Data\Setup_Test\Input_Test'

# Where should the combined file be stored?
output_path = r'C:\Users\lbongartz\Desktop\Reservoir Computing\Data\Setup_Test'

if __name__ == '__main__':
    input_path = Path(
        path)

        #r'C:\Users\Steiner\Documents\Python\SPRInd-challenge\data\training'
        #r'\input')

    all_input_files = list(sorted(input_path.glob("*.csv")))
    num_files = len(all_input_files)

    input_sequence = [None] * num_files
    for k, input_file in enumerate(all_input_files):

        print(input_file)

        len_zeros = round(seconds_zeros * rate)
        df = pd.read_csv(input_file, index_col=None)
        df_zeros = pd.DataFrame(np.zeros(shape=(len_zeros, 6)),
                                columns=df.columns)
        input_sequence[k] = df.append(df_zeros, ignore_index=True)

    input_sequence = pd.concat(input_sequence) + y_offset

    plot_array = input_sequence.to_numpy()
    N = len(plot_array)
    plot_time = np.linspace(0, N/rate, N)
    plt.plot(plot_time, plot_array[:,1:5])
    plt.show()

    input_sequence.to_csv(output_path + '/Files_combined.csv', index = False)
