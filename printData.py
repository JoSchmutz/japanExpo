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
# import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal
import scipy
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

ws = create_connection('ws://127.0.0.1:8080') # TOBE MODIFIED
reply = ws.recv();
serverAnswer = json.loads(reply);
pyId = serverAnswer['DATA'];

print "Id for server is : " , pyId


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
print('--- Creating process ---')
# process = Popen(['/usr/local/bin/node', 'openBCIDataStream.js'], stdout=PIPE)
# queue = Queue()
# thread = Thread(target=enqueue_output, args=(process.stdout, queue))
# thread.daemon = True # kill all on exit
# thread.start()
process = Popen(['/usr/local/bin/node', 'openBCIDataStream.js'], stdout=PIPE)
queue = Queue()
thread = Thread(target=enqueue_output, args=(process.stdout, queue))
thread.daemon = True # kill all on exit
thread.start()


# try:
#     pipe = subprocess.Popen('node openBCIDataStream.js', stdout=subprocess.PIPE,stderr=subprocess.STDOUT, shell=True)
# except Exception as e:
#     logging.error(str(e))
# queue = Queue()
# thread = Thread(target=enqueue_output, args=(pipe.stdout, queue))
# thread.daemon = True # kill all on exit
# thread.start()

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
nb = np.zeros(200)
while True:
    try:
        # the first while loop builds the buffers for 1 second, data are then processed by the second loop
        while (cpt < buffersize*nb_channels)  :
            buffer_1.append(queue.get_nowait())
            #buffer_2.append(queue2.get_nowait())
            cpt += 1
            cpt2 = 0
            # print queue.get_nowait()

        while cpt2 < 1 :

            #print len(buffer_1) returns 800

            cpt2 += 1
            # buffer_1_array = np.asarray(buffer_1, dtype=np.float64)
            buffer_1_array = np.asarray(buffer_1)
            # print buffer_1_array
            # buffer_1_array[:].astype(float)
            # buffer_1_array = buffer_1_array_str.astype(np.float)
            # buffer_1_array.astype(np.float64)
            # for j in range(200):
            #     nb[j] = float(buffer_1_array[ind_channel_1][j])
            #


            # print f_buffer_1
            # print buffer_1_array.astype(float)
            # print buffer_1_array

            # print buffer_1_array[ind_channel_1]
            OPB1_data[0, :] = buffer_1_array[ind_channel_1]
            OPB1_data[1, :] = buffer_1_array[ind_channel_2]
            OPB1_data[2, :] = buffer_1_array[ind_channel_3]
            OPB1_data[3, :] = buffer_1_array[ind_channel_4]

            f_ch1 = filter_data(OPB1_data[0, :], fs_hz)
            f_ch2 = filter_data(OPB1_data[1, :], fs_hz)
            f_ch3 = filter_data(OPB1_data[2, :], fs_hz)
            f_ch4 = filter_data(OPB1_data[3, :], fs_hz)

            # plt.plot(f_ch1)
            # plt.plot(OPB1_data[0,:])
            # plt.show()

            # print f_ch1 - OPB1_data[0,:]

            OPB1_result = np.zeros(nb_channels)
            # print len(OPB1_data[0, :])

            for channel in range(4):
                OPB1_result[channel] = extract_freqbandmean(200, fs_hz, OPB1_data[channel,:], freqRange[0], freqRange[1])

            print 'CHAN1', OPB1_result[0] , 'CHAN2', OPB1_result[1] , 'CHAN3', OPB1_result[2] , 'CHAN4', OPB1_result[3]
            concentrationLevel = np.average([OPB1_result[0], OPB1_result[1], OPB1_result[2], OPB1_result[3]])
            print 'CONCENTRATION  LEVEL : ' , concentrationLevel
            # ws.send( json.dumps( { 'FROM' : pyId , 'TO' : 'UNITY' , 'CMD' : 'SAVE' , 'DATA' : { 'ID' : '1' , 'CHAN1' : OPB1_result[0] , 'CHAN2' : OPB1_result[1] , 'CHAN3' : OPB1_result[2] , 'CHAN4' : OPB1_result[3] }  } ) );

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
