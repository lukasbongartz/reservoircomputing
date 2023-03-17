# L.Bongartz 15.03.2023
#
# This script is for giving functions (e.g., sin, square...) as the output of the MCC (aka input of the reservoir). 
# It is NOT the script for using data (e.g., speech data, heart beats). Please use Data_Output.py for this
#
# When you run this script, a window will show up with a snippet of the function you're inserting. The output will start
# once you close this window.


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

try:
    from Config_File_Dont_Touch import config_first_detected_device
except ImportError:
    from .Config_File_Dont_Touch import config_first_detected_device


# Insert your parameters here

time = 10  # How long the signal should be applied (in s)
rate = 500 # At what rate the signal should be applied
plot = True # Should the output be plotted? Better leave it as True, it's like a security break to doublecheck your input. 
            # Otherwise insert "False"



# You will probably NOT need to set anything in run_example()
def run_example():

    # Only relevant if you use the output of multiple boards.
    board_num = 0

    use_device_detection = False
    dev_id_list = []
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

        points_per_channel = time * rate
        total_count = points_per_channel * num_chans
        sample_time = points_per_channel/rate
        print('Sample time = ' + str(sample_time) + "s")

        ao_range = ao_info.supported_ranges[0]
 
        # Apply 0V to start
        v_start = 0
        print('Applying ' +str(v_start) + 'V to start')
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
        v_final = 0
        print('\nApplying ' + str(v_final) + 'V to finish')
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


# You will need to set a few things here:
def add_example_data(board_num, data_array, ao_range, num_chans, rate,
                     points_per_channel):
    
    #################################################
    # Set the parameters for the 4 channels here

    freq_Ch0 = 5
    freq_Ch1 = 5
    freq_Ch2 = 5
    freq_Ch3 = 5
    
    amplitude_Ch0 = 1
    amplitude_Ch1 = 1
    amplitude_Ch2 = 1
    amplitude_Ch3 = 1

    y_offset_Ch0 = 0
    y_offset_Ch1 = 0
    y_offset_Ch2 = 0
    y_offset_Ch3 = 0
    
    duty = 0.5  # Duty cycle, if you use a square wave. Don't be surprised, when the script is a bit slower 
                # when running the sqaure wave.

    #################################################
    
    def square(amp, freq, duty, y_off):
        t = np.linspace(0, time, points_per_channel, endpoint=False)
        output = amp*signal.square(2 * np.pi * freq * t, duty=duty) + y_off
        return output
        
    frequencies = [freq_Ch0, freq_Ch1, freq_Ch2, freq_Ch3]
    amplitude = [amplitude_Ch0, amplitude_Ch1, amplitude_Ch2, amplitude_Ch3]
    y_offset = [y_offset_Ch0, y_offset_Ch1, y_offset_Ch2, y_offset_Ch3]

    points_per_channel = time * rate
    value_array = []
    Ch0, Ch1, Ch2, Ch3 = [],[],[],[]
    data_index = 0
    for point_num in range(points_per_channel):
        for channel_num in range(num_chans):

            freq = frequencies[channel_num]
            amp = amplitude[channel_num]
            y_off = y_offset[channel_num]

            #################################################
            # Function selection
            # Choose between sin, sqaure o 0V for each channel by commenting out

            if channel_num == 0:

                value = amp * sin(2 * pi * freq * point_num / rate) + y_off 
                #value = square(amp, freq, duty, y_off)[point_num]
                #value = 0 
                Ch0.append(value)

            elif channel_num == 1:

                value = amp * sin(2 * pi * freq * point_num / rate) + y_off 
                #value = square(amp, freq, duty, y_off)[point_num]
                #value = 0 
                Ch1.append(value)

            elif channel_num == 2:

                value = amp * sin(2 * pi * freq * point_num / rate) + y_off 
                #value = square(amp, freq, duty, y_off)[point_num]
                #value = 0 

                Ch2.append(value)
            else:

                value = amp * sin(2 * pi * freq * point_num / rate) + y_off 
                #value = square(amp, freq, duty, y_off)[point_num]
                #value = 0 
                
                Ch3.append(value)
            #################################################

            raw_value = ul.from_eng_units(board_num, ao_range, value)
            data_array[data_index] = raw_value
            data_index += 1
            value_array.append(value)

    time_array = np.linspace(0, time, time*rate)
    if plot == True:
        plt.plot(time_array, Ch0, label = 'Channel 0')
        plt.plot(time_array, Ch1, label = 'Channel 1')
        plt.plot(time_array, Ch2, label = 'Channel 2')
        plt.plot(time_array, Ch3, label = 'Channel 3')
        plt.title('Output of DAC / Input to Reservoir')
        plt.legend()
        plt.xlim([0, 2])
        plt.show()
    return frequencies


if __name__ == '__main__':
    run_example()