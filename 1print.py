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


FreqRange = 'XXII_beta'


if FreqRange == '':
    logging.warning('No frequency passed as argument')

if FreqRange == 'alpha':
    freqRange = np.array([8, 12])
elif FreqRange == 'gamma':
    freqRange = np.array([25, 50])
elif FreqRange == 'beta':
    freqRange = np.array([12, 25])
elif FreqRange == 'theta':
    freqRange = np.array([4, 7])
elif FreqRange == 'XXII_beta':
    freqRange = np.array([15, 23])
elif FreqRange == 'XXII_gamma':
    freqRange = np.array([38, 40])

websocket.enableTrace(True)

pyId = -1;

ws = create_connection('ws://127.0.0.1:9030') # TOBE MODIFIED
reply = ws.recv();
serverAnswer = json.loads(reply);
pyId = serverAnswer['DATA'];

print("Id for server is : " , pyId)


cpt = 0
buffersize = 200 # there are 200 points for the four channels
nb_channels = 4
buffer_1 = []
#buffer_2 = []
ind_2_remove_in_buffer1 = []
ind_channel_1 = []
ind_channel_2 = []
ind_channel_3 = []
ind_channel_4 = []
NFFT = 200
fs_hz = 200
#overlap = NFFT - 30
cpt2 = 0
OPB1_newMean_uv = 0
#OPB2_newMean_uv = 0
sample_number = 0
#OPB1_oldMean_uv = 5E-13
#OPB2_oldMean_uv = 5E-13
OPB1_mean_array_uv = np.array([])
#OPB2_mean_array_uv = np.array([])
OPB1_data = np.zeros((nb_channels, buffersize))
#OPB2_data = np.zeros((nb_channels, buffersize))

#On MAC/UNIX
#process1 = Popen(['/usr/local/bin/node', 'openBCIDataStream.js'], stdout=PIPE)
print('--- Creating process ---')
try:
    pipe1 = subprocess.Popen('node D:/LivWorkspace/japanExpo/openBCIDataStream.js', stdout=subprocess.PIPE,stderr=subprocess.STDOUT, shell=True)
except Exception as e:
    logging.error(str(e))
queue1 = Queue()
thread1 = Thread(target=enqueue_output, args=(pipe1.stdout, queue1))
thread1.daemon = True # kill all on exit
thread1.start()

#On MAC/UNIX
#print('--- Creating process #2 ---')
#try:
#    pipe2 = subprocess.Popen('node D:/LivWorkspace/japanExpo/openBCIDataStream.js', stdout=subprocess.PIPE,stderr=subprocess.STDOUT, shell=True)
#except Exception as e:
#    logging.error(str(e))
#queue2 = Queue()
#thread2 = Thread(target=enqueue_output, args=(pipe2.stdout, queue1))
#thread2.daemon = True # kill all on exit
#thread2.start()

# the following loop saves the index of the buffer that are interesting, without the channel index : 0 [5]
for ind in range(0, buffersize):
    ind_channel_1.append(ind*4)
    ind_channel_2.append(ind*4+1)
    ind_channel_3.append(ind*4+2)
    ind_channel_4.append(ind*4+3)

while True:
    try:
        # the first while loop builds the buffers for 1 second, data are then processed by the second loop
        while (cpt < buffersize*4)  :
            buffer_1.append(queue1.get_nowait())
            #print(queue1.get_nowait())
            #buffer_2.append(queue2.get_nowait())
            #buffer_1 = filter_data(buffer_1, fs_hz)
            cpt += 1
            cpt2 = 0

        while cpt2 < 1 :
            #print(buffer_1)
            cpt2 += 1
            #buffer_1_array = np.asarray(buffer_1, dtype=np.float64)
            buffer_1_array = np.asarray(buffer_1)
            
            #print buffer_1_array
            #print OPB1_data
            #print len(buffer_1_array) #returns 800
            #buffer_1_array.astype(np.float64)
            #print buffer_1_array
            OPB1_data[0, :] = buffer_1_array[ind_channel_1]
            #print OPB1_data
            OPB1_data[1, :] = buffer_1_array[ind_channel_2]
            OPB1_data[2, :] = buffer_1_array[ind_channel_3]
            OPB1_data[3, :] = buffer_1_array[ind_channel_4]
            OPB1_result = np.zeros(nb_channels)

            #print OPB1_data[0,:]
            for channel in range(4):
                OPB1_result[channel] = extract_freqbandmean(200, fs_hz, OPB1_data[channel,:], freqRange[0], freqRange[1])

            #print(OPB1_result[0])
            ws.send( json.dumps( { 'FROM' : pyId , 'TO' : 'UNITY' , 'CMD' : 'SAVE' , 'DATA' : { 'ID' : '1' , 'CHAN1' : OPB1_result[0] , 'CHAN2' : OPB1_result[1] , 'CHAN3' : OPB1_result[2] , 'CHAN4' : OPB1_result[3] }  } ) );

            #buffer_2_array = np.asarray(buffer_2, dtype=np.float64)
            #OPB2_data[0, :] = buffer_2_array[ind_channel_1]
            #OPB2_data[1, :] = buffer_2_array[ind_channel_2]
            #OPB2_data[2, :] = buffer_2_array[ind_channel_3]
            #OPB2_data[3, :] = buffer_2_array[ind_channel_4]
            #OPB2_result = np.zeros(nb_channels)

            #OPB2_result = wave_amplitude(OPB2_data_channel_1, fs_hz, NFFT, overlap, buffersize, freqRange )
            #for channel in range(4):
            #    OPB2_result[channel] = extract_freqbandmean(200, fs_hz, OPB2_data[channel,:], freqRange[0], freqRange[1])

            #ws.send( json.dumps( { 'FROM' : 'PY' , 'TO' : 'UNITY' , 'CMD' : 'SAVE' , 'DATA' : { 'ID' : '1' , 'CHAN1' : OPB2_result[0] , 'CHAN2' : OPB2_result[1] , 'CHAN3' : OPB2_result[2] , 'CHAN4' : OPB2_result[3] }  } ) );

            cpt = 0
            buffer_1 = []
            #buffer_2 = []

    except Empty:
        continue # do stuff
    else:
        str(buffer_1)
        #str(buffer_2)
        #sys.stdout.write(char)
