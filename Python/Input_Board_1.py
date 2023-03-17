# L.Bongartz 15.03.2023
#
# This script is for reading data (e.g., speech data, heart beats) as the input of the MCC (aka output of the reservoir). 
# For this, the script needs to be run in parallel with an outout script in a second terminal. See the Read-me file or contact me,
# if you don't know how to do this. To read the full data, it is important that the scan time (see below) is longer than the time of
# data you sent in. You can set it to be significantly longer, since this script will stop anyway, once your input file is finished.
# It will then be stored as a .csv-file


from __future__ import absolute_import, division, print_function
from builtins import *  # @UnusedWildImport

from ctypes import c_double, cast, POINTER, addressof, sizeof
from time import sleep
from datetime import datetime
import os
from pathlib import Path

from mcculw import ul
from mcculw.enums import ScanOptions, FunctionType, Status, AnalogInputMode
from mcculw.device_info import DaqDeviceInfo
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.fft import rfft, rfftfreq

try:
    from Config_File_Dont_Touch import config_first_detected_device
except ImportError:
    from .Config_File_Dont_Touch import config_first_detected_device

#################################################
# Insert your parameters here

rate = 500 # At what rate the signal should be applied. The default of the speech_data is 100Hz. 
            # I recommend matching the rate of input and output.

input_scan_time = 100 # How long the output should be scanned (in s). Should be longer than your input (as defined in x_Output.py).

# What the highest input channel that you use on this device?
highest_input_channel = 0

# Do you want to plot the FFT?
FFT = False # True or False

# How should the output file be named?
file_name = 'Board1_Test.csv'

# Where should the output file be stored? 
# In this folder, a folder with todays date will be created, where the data will be stored
parent_dir = Path('C:/Users/lbongartz/Desktop/Reservoir Computing/Data/Setup_Test/Output_Test')


#################################################


# You will probably NOT need to set anything in run_example()
def run_example(board_num):

    now = datetime.now()
    date_time = now.strftime('%Y%m%d')
    path = os.path.join(parent_dir, date_time)
    
    # Create directory of todays date
    try: 
        os.mkdir(path)
    except OSError as error:
        print()  
    
    # Check, if file is already present
    check_file = os.path.exists(path + '\\' + file_name)

    if check_file == True:
        answer = input('File already exists, it will be overwritten! Continue anyway? \n(y/n) ')

        if answer.lower().startswith("y"):
            print('\n')
            print('Alright, as you like.')
            print('\n')

        elif answer.lower().startswith("n"):
            print('\n')
            print('Next time better change the name!')
            print('\n')
            exit()
    else:
        pass

    use_device_detection = False
    dev_id_list = []
    board_num = board_num
    memhandle = None
    input_mode = AnalogInputMode.SINGLE_ENDED
    specify_channels = True

    if specify_channels == True:
        highest_chan = highest_input_channel

    # The size of the UL buffer to create, in seconds. Default is 2s
    buffer_size_seconds = 2
    # The number of buffers to write. After this number of UL buffers are
    # written to file, the example will be stopped.
    num_buffers_to_write = input_scan_time/buffer_size_seconds

    scan_time = buffer_size_seconds * num_buffers_to_write
    total_points = scan_time * rate
    print('Scan time = ' + str(scan_time) + 's')
    print('Expect ' + str(total_points) + ' data points in total')

    try:
        if use_device_detection:
            config_first_detected_device(board_num, dev_id_list)
            ul.a_input_mode(board_num, input_mode)  

        daq_dev_info = DaqDeviceInfo(board_num)
        if not daq_dev_info.supports_analog_input:
            raise Exception('Error: The DAQ device does not support '
                            'analog input')

        print('\nActive DAQ device: ', daq_dev_info.product_name, ' (',
              daq_dev_info.unique_id, ')\n', sep='')
        print('NOW you can close the output window to start the experiment.\n')

        ai_info = daq_dev_info.get_ai_info()

        low_chan = 0
        if specify_channels == True:
            high_chan = highest_chan
        else:
            high_chan = max(3, ai_info.num_chans - 1)
        
        num_chans = high_chan - low_chan + 1
        
        
        # Create a circular buffer that can hold buffer_size_seconds worth of
        # data, or at least 10 points (this may need to be adjusted to prevent
        # a buffer overrun)
        points_per_channel = max(rate * buffer_size_seconds, 10)

        # Some hardware requires that the total_count is an integer multiple
        # of the packet size. For this case, calculate a points_per_channel
        # that is equal to or just above the points_per_channel selected
        # which matches that requirement.
        if ai_info.packet_size != 1:
            packet_size = ai_info.packet_size
            remainder = points_per_channel % packet_size
            if remainder != 0:
                points_per_channel += packet_size - remainder

        ul_buffer_count = points_per_channel * num_chans

        # Write the UL buffer to the file num_buffers_to_write times.
        points_to_write = ul_buffer_count * num_buffers_to_write

        # When handling the buffer, we will read 1/10 of the buffer at a time
        write_chunk_size = int(ul_buffer_count / 10)

        ai_range = ai_info.supported_ranges[0]

        scan_options = (ScanOptions.BACKGROUND | ScanOptions.CONTINUOUS |
                        ScanOptions.SCALEDATA)

        memhandle = ul.scaled_win_buf_alloc(ul_buffer_count)

        # Allocate an array of doubles temporary storage of the data
        write_chunk_array = (c_double * write_chunk_size)()

        # Check if the buffer was successfully allocated
        if not memhandle:
            raise Exception('Failed to allocate memory')

        # Start the scan
        ul.a_in_scan(
            board_num, low_chan, high_chan, ul_buffer_count,
            rate, ai_range, memhandle, scan_options)

        status = Status.IDLE
        # Wait for the scan to start fully
        while status == Status.IDLE:
            status, _, _ = ul.get_status(board_num, FunctionType.AIFUNCTION)

        # Create a file for storing the data
        with open(path + '\\' + file_name, 'w') as f:
            print('Writing data to ' + file_name, end='')

            # Write a header to the file
            for chan_num in range(low_chan, high_chan + 1):
                f.write('Channel ' + str(chan_num) + ',')
            f.write(u'\n')

            # Start the write loop
            plot_data = []
            prev_count = 0
            prev_index = 0
            write_ch_num = low_chan
            while status != Status.IDLE:
                # Get the latest counts
                status, curr_count, _ = ul.get_status(board_num,
                                                      FunctionType.AIFUNCTION)

                new_data_count = curr_count - prev_count

                # Check for a buffer overrun before copying the data, so
                # that no attempts are made to copy more than a full buffer
                # of data
                if new_data_count > ul_buffer_count:
                    # Print an error and stop writing
                    ul.stop_background(board_num, FunctionType.AIFUNCTION)
                    print('A buffer overrun occurred')
                    break
                stop = 0

                # Check if a chunk is available
                if new_data_count > write_chunk_size:
                    wrote_chunk = True
                    # Copy the current data to a new array

                    # Check if the data wraps around the end of the UL
                    # buffer. Multiple copy operations will be required.
                    if prev_index + write_chunk_size > ul_buffer_count - 1:
                        first_chunk_size = ul_buffer_count - prev_index
                        second_chunk_size = (
                            write_chunk_size - first_chunk_size)

                        # Copy the first chunk of data to the
                        # write_chunk_array
                        ul.scaled_win_buf_to_array(
                            memhandle, write_chunk_array, prev_index,
                            first_chunk_size)

                        # Create a pointer to the location in
                        # write_chunk_array where we want to copy the
                        # remaining data
                        second_chunk_pointer = cast(addressof(write_chunk_array)
                                                    + first_chunk_size
                                                    * sizeof(c_double),
                                                    POINTER(c_double))

                        # Copy the second chunk of data to the
                        # write_chunk_array
                        ul.scaled_win_buf_to_array(
                            memhandle, second_chunk_pointer,
                            0, second_chunk_size)
                    else:
                        # Copy the data to the write_chunk_array
                        ul.scaled_win_buf_to_array(
                            memhandle, write_chunk_array, prev_index,
                            write_chunk_size)

                    # Check for a buffer overrun just after copying the data
                    # from the UL buffer. This will ensure that the data was
                    # not overwritten in the UL buffer before the copy was
                    # completed. This should be done before writing to the
                    # file, so that corrupt data does not end up in it.
                    status, curr_count, _ = ul.get_status(
                        board_num, FunctionType.AIFUNCTION)
                    if curr_count - prev_count > ul_buffer_count:
                        # Print an error and stop writing
                        ul.stop_background(board_num, FunctionType.AIFUNCTION)
                        print('A buffer overrun occurred')
                        break

                    for i in range(write_chunk_size):
                        f.write(str(write_chunk_array[i]) + ',')
                        write_ch_num += 1
                        if write_ch_num == high_chan + 1:
                            write_ch_num = low_chan
                            f.write(u'\n')
                        #plot_data.append(str(write_chunk_array[i]))
                else:
                    wrote_chunk = False

                if wrote_chunk:
                    # Increment prev_count by the chunk size
                    prev_count += write_chunk_size
                    # Increment prev_index by the chunk size
                    prev_index += write_chunk_size
                    # Wrap prev_index to the size of the UL buffer
                    prev_index %= ul_buffer_count

                    if prev_count >= points_to_write:
                        break
                    print('.', end='')
                else:
                    # Wait a short amount of time for more data to be
                    # acquired.
                    sleep(0)

        ul.stop_background(board_num, FunctionType.AIFUNCTION)
    except Exception as e:
        print('\n', e)
    finally:
        print('Done')
        if memhandle:
            # Free the buffer in a finally block to prevent  a memory leak.
            ul.win_buf_free(memhandle)
        if use_device_detection:
            ul.release_daq_device(board_num)

    plot_data = pd.read_csv(path + '\\' + file_name, sep=',')

    time = plot_data.index/total_points*scan_time
    plot_data['Time'] = time
    first_column = plot_data.pop('Time')
    plot_data.insert(0, 'Time', first_column)

    plot_data.iloc[:,:num_chans+1].plot(x='Time')
    plot_data.iloc[:,:num_chans+1].to_csv(path + '\\' + file_name, sep='\t')
    plt.title('Input of Board 1 / Output of Reservoir')
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage (V)')
    plt.legend(loc = 6)

    if FFT == True:    
        maxfreq = 10
        for chan in range(num_chans):
            plt.figure()
            chunk_size = 1 #single frequencies
            xf = rfftfreq(len(time), 1/rate)
            yf = rfft(plot_data.iloc[:,chan+1].to_numpy())
            num_chunk = len(xf) // chunk_size
            sn = []
            for chunk in range(0, num_chunk):
                sn.append(np.mean(yf[chunk*chunk_size:(chunk+1)*chunk_size]**2))
            
            plt.title('FFT of Channel '+str(chan) + ' (Board 1)')
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Magnitude')

            plt.stem(xf, abs(yf), label = 'Channel '+str(num_chans), markerfmt=' ')
            plt.xlim([0,25])

    plt.show()
 
if __name__ == '__main__':
    sleep(2)
    run_example(1)