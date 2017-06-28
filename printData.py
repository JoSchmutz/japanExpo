import sys
from subprocess import Popen, PIPE
from threading  import Thread
from Queue      import Queue, Empty
from subprocess import call
import subprocess
import socket
from threading import *
import time
import signal
import matplotlib.mlab as mlab
import numpy as np
import pandas as pd
from scipy import signal
import json
from requests import *
import datetime
import math
import json
import pprint
import websocket
from websocket import create_connection
from functions import *

def enqueue_output(out, queue):
    while True:
        lines = out.readline()
        out.flush()
        queue.put(lines)

websocket.enableTrace(True)

ws = create_connection('ws://192.168.0.21:8080') # TOBE MODIFIED

freqRange = 'XXII'
cpt = 0
buffersize = 200 # there are 200 points for the four channels
buffer_1 = []
buffer_2 = []
ind_2_remove_in_buffer1 = []
ind_channel_1 = []
ind_channel_2 = []
ind_channel_3 = []
ind_channel_4 = []
NFFT = 200
fs_hz = 200
overlap = NFFT - 30
cpt2 = 0
OPB1_newMean_uv = 0
OPB2_newMean_uv = 0
OPB1_data = data = np.zeros((nb_channels, buffersize))
OPB2_data = data = np.zeros((nb_channels, buffersize))

sample_number = 0
OPB1_oldMean_uv = 5E-13
OPB2_oldMean_uv = 5E-13
OPB1_mean_array_uv = np.array([])
OPB2_mean_array_uv = np.array([])

process1 = Popen(['/usr/local/bin/node', 'openBCIDataStream.js'], stdout=PIPE)
queue1 = Queue()
thread1 = Thread(target=enqueue_output, args=(process1.stdout, queue1))
thread1.daemon = True # kill all on exit
thread1.start()

time.sleep(0.3)
process2 = subprocess.Popen(['/usr/local/bin/node', 'openBCIDataStream.js'], stdout=PIPE)
queue2 = Queue()
thread2 = Thread(target=enqueue_output, args=(process2.stdout, queue2))
thread2.daemon = True # kill all on exit
thread2.start()


# the following loop saves the index of the buffer that are interesting, without the channel index : 0 [5]
for ind in range(0, buffersize):
    ind_channel_1.append(ind*5+1)
    ind_channel_2.append(ind*5+2)
    ind_channel_3.append(ind*5+3)
    ind_channel_4.append(ind*5+4)

while True:
    try:
        # the first while loop builds the buffers for 1 second, data are then processed by the second loop
        while (cpt < buffersize*5)  :
            buffer_1.append(queue1.get_nowait())
            buffer_2.append(queue2.get_nowait())
            cpt += 1
            cpt2 = 0

        while cpt2 <1 :
            cpt2 += 1
            buffer_1_array = np.asarray(buffer_1, dtype=np.float64)
            buffer_2_array = np.asarray(buffer_2, dtype=np.float64)

            OPB1_data[0, :] = buffer_1_array[ind_channel_1]
            OPB1_data[1, :] = buffer_1_array[ind_channel_2]
            OPB1_data[2, :] = buffer_1_array[ind_channel_3]
            OPB1_data[3, :] = buffer_1_array[ind_channel_4]
            OPB1_result = np.zeros(nb_channels)

            OPB1_result = wave_amplitude(OPB1_data_channel_1, fs_hz, NFFT, overlap, buffersize, freqRange )
            for channel in range(4):
                OPB1_result[channel] = extract_freqbandmean(200, fs_hz, OPB1_data[channel,:], freqRange[0], freqRange[1])

            ws.send(json.dumps([json.dumps({'ID': '1', 'data': {'channel1': OPB1_result[0], 'channel2': OPB1_result[1], 'channel3': OPB1_result[2], 'channel4': OPB1_result[3]}} )]))
            OPB2_data[0, :] = buffer_1_array[ind_channel_1]
            OPB2_data[1, :] = buffer_1_array[ind_channel_2]
            OPB2_data[2, :] = buffer_1_array[ind_channel_3]
            OPB2_data[3, :] = buffer_1_array[ind_channel_4]
            OPB2_result = np.zeros(nb_channels)

            OPB2_result = wave_amplitude(OPB2_data_channel_1, fs_hz, NFFT, overlap, buffersize, freqRange )
            for channel in range(4):
                OPB2_result[channel] = extract_freqbandmean(200, fs_hz, OPB2_data[channel,:], freqRange[0], freqRange[1])

            ws.send(json.dumps([json.dumps({'ID': '1', 'data': {'channel1': OPB2_result[0], 'channel2': OPB2_result[1], 'channel3': OPB2_result[2], 'channel4': OPB2_result[3]}} )]))

            # print "OPENBCI 1 : " + freqRange + " mean for each channel: \n CHANNEL 1:  ", OPB1_result1, "    CHANNEL 2 : ", OPB1_result2, "    CHANNEL 3 : ", OPB1_result3, "    CHANNEL 4 : ", OPB1_result4
            # print "OPENBCI 2 : " + freqRange + " mean for each channel: \n CHANNEL 1:  ", OPB2_result1, "    CHANNEL 2 : ", OPB2_result2, "    CHANNEL 3 : ", OPB2_result3, "    CHANNEL 4 : ", OPB2_result4


            cpt = 0
            # OPB1_oldMean_uv = OPB1_newMean_uv
            # OPB2_oldMean_uv = OPB2_newMean_uv
            buffer_1 = []
            buffer_2 = []

    except Empty:
        continue # do stuff
    else:
        # wave_amplitude(data, fs_hz, NFFT, overlap, 'alpha')
        str(buffer_1)
        str(buffer_2)
        #sys.stdout.write(char)
