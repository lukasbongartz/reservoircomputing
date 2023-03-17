# L.Bongartz 15.03.2023
#
# This script is for giving data (e.g., speech data, heart beats) as the output of the MCC (aka input of the reservoir). 
# It is NOT the script for using functions (e.g., sin, square...). Please use Functions_Output.py for this.
#
# When you run this script, a window will show up with a snippet of the function you're inserting. The output will start
# once you close this window.
#
# The data needs to be inserted as a single file. For preparing this, use Data_perparations.py
# If everything works out well, you will not really need to set anything within this scripts, but just run it.

from __future__ import absolute_import, division, print_function
from builtins import *  

from ctypes import cast, POINTER, c_ushort
from math import pi, sin, cos, tanh
from time import sleep

from mcculw import ul
from mcculw.enums import ScanOptions, FunctionType, Status
from mcculw.device_info import DaqDeviceInfo
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
import pandas as pd
import os

try:
    from Config_File_Dont_Touch import config_first_detected_device
except ImportError:
    from .Config_File_Dont_Touch import config_first_detected_device

#################################################


# Insert your parameters here

rate = 100 # At what rate the signal should be applied. The default of the speech_data is 100Hz

# In which folder is the input file located?
path = 'C:/Users/lbongartz/Desktop/Reservoir Computing/Data/Setup_Test'

# Filename?
filename = 'Files_combined.csv'

#################################################

board_num = 0

directory = os.fsencode(path)

Speech_Time = []
Speech_Filter1 = []
Speech_Filter2 = []
Speech_Filter3 = []
Speech_Filter4 = []
Target = []

num_files = len(os.listdir(directory))
for file in os.listdir(directory):
    Data = pd.read_csv(path+'/'+filename, delimiter=',').to_numpy()
    Speech_Time.append(Data[:,0])
    Speech_Filter1.append(Data[:,1])
    Speech_Filter2.append(Data[:,2])
    Speech_Filter3.append(Data[:,3])
    Speech_Filter4.append(Data[:,4])
    Target.append(Data[:,5])

for sample in [0]:
    time = len(Data)/rate

    rate = int(len(Speech_Time[sample])/time)
    points_per_channel = int(time * rate)

    Speech_Time = Speech_Time[sample]
    Speech_Filter1 = Speech_Filter1[sample]
    Speech_Filter2 = Speech_Filter2[sample]
    Speech_Filter3 = Speech_Filter3[sample]
    Speech_Filter4 = Speech_Filter4[sample]
    Target = Target[sample]

# You will probably NOT need to set anything in run_example()
def run_example():
    use_device_detection = True
    dev_id_list = []
    board_num = 0
    memhandle = None

    try:
        if use_device_detection:
            config_first_detected_device(board_num, dev_id_list)

        daq_dev_info = DaqDeviceInfo(board_num)
        if not daq_dev_info.supports_analog_output:
            raise Exception('Error: The DAQ device does not support '
                            'analog output')

        print('\nActive DAQ device: ', daq_dev_info.product_name, ' (',
              daq_dev_info.unique_id, ')\n', sep='')

        ao_info = daq_dev_info.get_ao_info()

        low_chan = 0
        high_chan = min(3, ao_info.num_chans - 1)
        num_chans = high_chan - low_chan + 1


        #points_per_channel = time * rate
        total_count = points_per_channel * num_chans
        sample_time = points_per_channel/rate
        print('Sample time = ' + str(sample_time) + "s")

        ao_range = ao_info.supported_ranges[0]

        print('Applying 0V to start')
        v_start = 0
        for channel_num in range(num_chans): 
            ul.v_out(board_num, channel_num, ao_range, v_start, options=0)
        status = Status.IDLE
        while status != Status.IDLE:
            print('.', end='')

            # Slow down the status check so as not to flood the CPU
            sleep(0.5)

            status, _, _ = ul.get_status(board_num, FunctionType.AOFUNCTION)
        print('')
        # Allocate a buffer for the scan
        memhandle = ul.win_buf_alloc(total_count)
        # Convert the memhandle to a ctypes array
        # Note: the ctypes array will no longer be valid after win_buf_free
        # is called.
        # A copy of the buffer can be created using win_buf_to_array
        # before the memory is freed. The copy can be used at any time.
        ctypes_array = cast(memhandle, POINTER(c_ushort))

        # Check if the buffer was successfully allocated
        if not memhandle:
            raise Exception('Error: Failed to allocate memory')

        frequencies = add_example_data(board_num, ctypes_array, ao_range,
                                       num_chans, rate, points_per_channel)

        for ch_num in range(low_chan, high_chan + 1):
            print('Channel', ch_num, 'Output Signal Frequency:',
                  frequencies[ch_num - low_chan])

        # Start the scan
        ul.a_out_scan(board_num, low_chan, high_chan, total_count, rate,
                      ao_range, memhandle, ScanOptions.BACKGROUND)
    

        # Wait for the scan to complete
        print('Waiting for output scan to complete...', end='')
        status = Status.RUNNING
        while status != Status.IDLE:
            print('.', end='')

            # Slow down the status check so as not to flood the CPU
            sleep(0.5)

            status, _, _ = ul.get_status(board_num, FunctionType.AOFUNCTION)
        print('')
        # Apply 0V at end
        print('Applying 0V to finish')
        v_final = 0
        for channel_num in range(num_chans): 
            ul.v_out(board_num, channel_num, ao_range, v_final, options=0)

        print('Scan completed successfully')
    except Exception as e:
        print('\n', e)
    #finally:
    #    if memhandle:
    #        # Free the buffer in a finally block to prevent a memory leak.
    #        ul.win_buf_free(memhandle)
    #    if use_device_detection:
    #        ul.release_daq_device(board_num)

# You will probably also not need to change anything here.
def add_example_data(board_num, data_array, ao_range, num_chans, rate,
                     points_per_channel):
    
    frequencies = [0,0,0,0]

    value_array = []
    Ch0, Ch1, Ch2, Ch3 = [],[],[],[]
    data_index = 0
    for point_num in range(len(Speech_Filter1)):
        for channel_num in range(num_chans):
            freq = frequencies[channel_num]
            if channel_num == 0:
                value = Speech_Filter1[point_num]
                Ch0.append(value)
            elif channel_num == 1:
                value = Speech_Filter2[point_num]
                Ch1.append(value)
            elif channel_num == 2:
                value = Speech_Filter3[point_num]
                Ch2.append(value)
            else:
                value = Speech_Filter4[point_num]
                Ch3.append(value)

            raw_value = ul.from_eng_units(board_num, ao_range, value)
            data_array[data_index] = raw_value
            data_index += 1
            value_array.append(value)

    plt.plot(np.arange(0,len(Ch0))/rate, Ch0, label = 'Channel 0')
    plt.plot(np.arange(0,len(Ch1))/rate, Ch1, label = 'Channel 1')
    plt.plot(np.arange(0,len(Ch2))/rate, Ch2, label = 'Channel 2')
    plt.plot(np.arange(0,len(Ch3))/rate, Ch3, label = 'Channel 3')
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage (V)')
    plt.legend()
    plt.show()
    return frequencies

if __name__ == '__main__':
    run_example()


