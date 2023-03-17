# Reservoir Computing Setup

L.Bongartz 16.03.2023

**Intro to using the MCC Daq Cards for reservoir computing**

In this folder, you find two subfolders, Python & Data. Python contains the code files to run the MCC
cards. Data contains the input (if used) and output data. Independent of whether you use functions
(sin, square...) or real data as the input, your output will be saved there.

At the moment, I plan to use only 4 output channels of the cards, i.e. 4 input channels to the reservoir, which is sufficient
for using 4 features. In case we want more (up to 8 would be possible), it is not a big deal. Just let me know and 
I will prepare it for you. I did, however, plan using up to 16 input channels, i.e. 16 output channels of the reservoir.

When talking about the setup, always keep in mind what input and output refer to:
	- Output of card = Input of reservoir
	- Input of card = Output of reservoir

**Python Folder**

There are 5 files in the Python folder that are of interest to you. Do not change the rest.

	Functions_Output.py
		
Let's you use mathematical functions (sin, square) as the output of the card. You need to set the time,
for how long the signal should be applied, the rate, and the individual parameters for the 4 channels. 
The latter happens within the function add_example_data(), where you have to set frequency, amplitude, and y_offset
for each of the 4 channels. In case you use a square wave, you can also set the duty cycle here.
		
For selecting which function (sin, square or 0V) you want to use as the output, scroll further down
and search for the comment "# Function selection". There, you choose the individual functions by
commenting out (inserting "#") the ones that you DON'T want to use. Don't be surprised that the
script is slower, when you use a square wave.

When you run the script, a window will pop up, displaying a 2s-snippet of your output functions. The signal
will be applied, once you close this window.

	Data_preparation.py
		
Only relevant, if you use a data set as the input. This file transforms the single input files
(spoken words, heartbeats...) into one single file, where you need to specify the rate, 
the time for how long 0V is applied inbetween (important when using the hysteresis) and
the y_offset (important when making the fibers more sensitive).

	Data_Output.py
		
Let's you use a dataset as the output of the card. You need to prepare this dataset beforehand with
the file Data_preparation.py. You need to set the rate, the folder, in which the (prepared) input file
is located, as well as the file name. 		

When you run the script, a window will pop up, displaying your output. The signal will be applied, 
once you close this window.

	Input_Boards_0.py
	
Let's you record the input with board 0 (0 as defined in the Instacal software, see below).
You need to set the recording rate (I recommend using the same rate as in your x_Output.py file), the
name of the output file and the folder's path, where the data should be stored. In case the script recognizes
a file of same name (for example because you forgot to change the name between your experiments), 
it will pause and ask, whether you want to continue. If you say yes, the particular file will be overwritten. 
If no, the script will be aborted.

	Input_Boards_1.py
	
The same as Input_Boards_0.py, but for using the input channels of a second board.


**Get started**

First, you need to download the Instacal-software from https://www.mccdaq.com/daq-software/instacal.aspx
In this software, you can set and test basic functions of the boards. Here is also where, if you use two boards, the indices
of board 0 and board 1 are assigned.

Then, go to your favorite python environment (I recommend VS Code) and open the Python Folder. I also recommend working
in a virtual environment (see https://code.visualstudio.com/docs/python/environments), since I already installed such a venv
for you in the Python folder. Open this venv, and you should be ready to go. In case you don't want to do that for
whatever reason, you need to import all the libraries and packages to your python environment (e.g., numpy, 
pathlib, mcculw etc.). Once this is set up, you should be ready to go.


**How to start an experiment**

Connect all the hardware.

- Output only:

	If you now want to only apply an output, for instance to grow fibers, all you need to do
	is to run Functions_Output.py. Set the parameters within this script and it should do the job. It doesn't matter 
	here, whether you run the script ordinary, through the debugger or in the terminal.

- Output and input simultaneously:

	Now it gets a bit tricky, but I will walk you through. What we need to do is to simultaneously run the output 
	(Function_Output.py or Data_Output.py) and input scripts. For this, you first want to specify your parameters (times, rates,
	filenames etc.) in the invidual scripts and make sure that the input scanning time is significantly longer than your output time. 
	This is crucial. Now you need to open two terminals, navigate to the python folder and run the scripts after each other (Terminal 1: 
	"python x_Output.py", Terminal 2: "python Input_Board_0.py). 
	
	IMPORTANT: Always run the Output script first, then the input script.

	From the output script, the window displaying your function/data will pop up. 

	IMPORTANT: DON'T close it immedeatly!

	Wait for the input script and answer the question if asked. The input script will then tell you, when you can close the window to start
	your experiment. 

	Wait for the output script to finish. Once your function/data is finished, it will again apply 0V and the input script will stop.
	You should be able to see this final 0V in the upcoming plot of the input script. Check for this, in order to verify that all your
	data has been recorded. If this is not the case, you first want to check whether your input time is really significantly
	longer than your output time. If yes, just repeat the experiment, maybe the buffer was not completely emptied. If the data is still 
	cut, you most likely need to increase the rates you use.

- Using more than 8 card inputs

	For using more than 8 card input channels, you need to connect two cards and check in Instacal that the indices 0 and 1 are
	assigned. Also, check that both cards are set to single-ended mode. You will then not only open two terminals, but three. In Terminal 1 you run your 		x_output.py file. In Terminal 2 & 3 you rund
	Input_Board_0.py and Input_Board_1.py. 
 
 
- More help:

	This will not be relevant to, as long as everything works fine. Otherwise, you might want to have a look at
	https://www.mccdaq.com/PDFs/Manuals/Mcculw_WebHelp/ULStart.htm and to the manual.

	




	


		 
