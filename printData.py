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


def filter_data(data, fs_hz):

    # filter the data to remove DC
    hp_cutoff_hz = 1.0
    b, a = signal.butter(2, hp_cutoff_hz / (fs_hz / 2.0), 'highpass')  # define the filter
    ff_data = signal.lfilter(b, a, data, 0)  # apply along the zeroeth dimension

    # filter from 5 to 35 Hz, helps remove 50Hz noise and replicates paper
    ## also helps remove the DC line noise (baseline drift)
    ## 125 is half the sampling rate (250Hz/2)
    b, a = signal.butter(4, (2.0 / (fs_hz / 2.0), 40.0 / (fs_hz / 2.0)), btype='bandpass')
    f_data = signal.lfilter(b, a, data, axis=0)

    # notch filter the data to remove 50 Hz and 100 Hz
    notch_freq_hz = np.array([50.0])  # these are the center frequencies
    for freq_hz in np.nditer(notch_freq_hz):  # loop over each center freq
        bp_stop_hz = freq_hz + 3.0 * np.array([-1, 1])  # set the stop band
        b, a = signal.butter(3, bp_stop_hz / (fs_hz / 2.0), 'bandstop')  # create the filter
        ff_data = signal.lfilter(b, a, f_data, 0)  # apply along the zeroeth dimension

    # return ff_data
    return f_data

def wave_amplitude(data, fs_hz, NFFT, overlap, length, frequenciesRange):
    data = np.asarray(data)
    data = data[:buffersize, :]
    f_eeg_data = filter_data(data, fs_hz)
    #t0 = time.time()

    if frequenciesRange == 'delta':
        wave_band_Hz = np.array([0.4, 4])
    elif frequenciesRange == 'theta':
        wave_band_Hz = np.array([4, 7])
    if frequenciesRange == 'alpha':
        wave_band_Hz = np.array([8, 12])
    elif frequenciesRange == 'beta':
        wave_band_Hz = np.array([12, 25])
    elif frequenciesRange == 'gamma':
        wave_band_Hz = np.array([25, 35])
    elif frequenciesRange == 'XXII':
        wave_band_Hz = np.array([20, 40])

    size = f_eeg_data.shape[1]

    mean_range = np.zeros((1, size))
    max_range = np.zeros((1, size))
    min_range = np.zeros((1, size))
    ratio = np.zeros((1, size))

    for channel in range(size):

        spec_PSDperHz, freqs, t_spec = mlab.specgram(f_eeg_data[20:, channel],
                                                     NFFT=NFFT,
                                                     Fs=fs_hz,
                                                     window=mlab.window_hanning,
                                                     noverlap=overlap)

        # convert the units of the spectral data
        spec_PSDperBin = spec_PSDperHz * fs_hz / float(NFFT)  # convert to "Power Spectral Density per bin"
        spec_PSDperBin = np.asarray(spec_PSDperBin)
        # print(spec_PSDperBin.shape) # from 1 to 110 Hz, step of 1Hz

        # take the average spectrum according to the time - axis 1
        bool_inds_wave_range = (freqs > wave_band_Hz[0]) & (freqs < wave_band_Hz[1])
        # freq_range_index = freqs[bool_inds_wave_range == 1]
        # freq_range_max = freq_range[max_range_idx]

        spec_PSDperBin_range = spec_PSDperBin[bool_inds_wave_range]
        mean_range[0][channel] = np.mean(spec_PSDperBin_range)
        # max_range[0][channel] = np.amax(spec_PSDperBin_range)
        # get the frequency of the max in each range alpha, beta, theta, gamma
        # max_range_idx = np.argmax(spec_PSDperBin_range)

    '''
    Get the median, max and min of the 4 channels
    '''

    med_range = np.median(mean_range[0][:])
    max_range = np.amax(mean_range[0][:])
    min_range = np.min(mean_range[0][:])

    results = [med_range, max_range, min_range]
    result = results[0]
    # print(med_gamma.type())

    return result

def enqueue_output(out, queue):
    while True:
        lines = out.readline()
        out.flush()
        queue.put(lines)

websocket.enableTrace(True)

ws = create_connection('ws://192.168.1.198:8080') # TOBE MODIFIED

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
data = []
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
            buffer_1.append([queue1.get_nowait()])
            buffer_2.append([queue2.get_nowait()])
            cpt += 1
            cpt2 = 0

        while cpt2 <1 :
            cpt2 += 1
            buffer_1_array = np.asarray(buffer_1, dtype=np.float64)
            buffer_2_array = np.asarray(buffer_2, dtype=np.float64)

            OPB1_data_channel_1 = buffer_1_array[ind_channel_1]
            OPB1_data_channel_2 = buffer_1_array[ind_channel_2]
            OPB1_data_channel_3 = buffer_1_array[ind_channel_3]
            OPB1_data_channel_4 = buffer_1_array[ind_channel_4]
            OPB1_result1 = wave_amplitude(OPB1_data_channel_1, fs_hz, NFFT, overlap, buffersize, freqRange )
            OPB1_result2 = wave_amplitude(OPB1_data_channel_2, fs_hz, NFFT, overlap, buffersize, freqRange )
            OPB1_result3 = wave_amplitude(OPB1_data_channel_3, fs_hz, NFFT, overlap, buffersize, freqRange )
            OPB1_result4 = wave_amplitude(OPB1_data_channel_4, fs_hz, NFFT, overlap, buffersize, freqRange )

            OPB2_data_channel_1 = buffer_2_array[ind_channel_1]
            OPB2_data_channel_2 = buffer_2_array[ind_channel_2]
            OPB2_data_channel_3 = buffer_2_array[ind_channel_3]
            OPB2_data_channel_4 = buffer_2_array[ind_channel_4]
            OPB2_result1 = wave_amplitude(OPB2_data_channel_1, fs_hz, NFFT, overlap, buffersize, freqRange )
            OPB2_result2 = wave_amplitude(OPB2_data_channel_2, fs_hz, NFFT, overlap, buffersize, freqRange )
            OPB2_result3 = wave_amplitude(OPB2_data_channel_3, fs_hz, NFFT, overlap, buffersize, freqRange )
            OPB2_result4 = wave_amplitude(OPB2_data_channel_4, fs_hz, NFFT, overlap, buffersize, freqRange )

            # OPB1_newMean_uv = np.average(OPB1_result2)
            # OPB2_newMean_uv = np.average(OPB2_result2)
            # the mean_array_uv gather all the means of the channel2, each second, to get the global mean of that channel
            # OPB1_mean_array_uv = np.append(OPB1_mean_array_uv, OPB1_newMean_uv)
            # OPB2_mean_array_uv = np.append(OPB2_mean_array_uv, OPB2_newMean_uv)

            # OPB1_spread_average = np.average(OPB1_mean_array_uv[-5:-1])
            # OPB2_spread_average = np.average(OPB2_mean_array_uv[-5:-1]) # the spread_average takes the 5 last Means in the array mean_array_uv, and get the mean of them

            # print "OPENBCI 1 : " + freqRange + " mean for each channel: \n CHANNEL 1:  ", OPB1_result1, "    CHANNEL 2 : ", OPB1_result2, "    CHANNEL 3 : ", OPB1_result3, "    CHANNEL 4 : ", OPB1_result4
            # print "OPENBCI 2 : " + freqRange + " mean for each channel: \n CHANNEL 1:  ", OPB2_result1, "    CHANNEL 2 : ", OPB2_result2, "    CHANNEL 3 : ", OPB2_result3, "    CHANNEL 4 : ", OPB2_result4
            ws.send(json.dumps([json.dumps({'ID': '1', 'data': {'channel1': OPB1_result1, 'channel2': OPB1_result2, 'channel3': OPB1_result3, 'channel4': OPB1_result4}} )]))
            ws.send(json.dumps([json.dumps({'ID': '2', 'data': {'channel1': OPB2_result1, 'channel2': OPB2_result2, 'channel3': OPB2_result3, 'channel4': OPB2_result4}} )]))

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
