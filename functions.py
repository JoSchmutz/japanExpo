import sys
from Queue      import Queue, Empty
from subprocess import call
import binascii
import time
import signal
import matplotlib.mlab as mlab
import numpy as np
import pandas as pd
import heapq
from scipy import signal
import json
from requests import *
import datetime
import math

def filter_data(data, fs_hz):
    '''
    filter from 2 to 50 Hz, helps remove 50Hz noise and replicates paper
    US : 60Hz, UE : 50Hz
    also helps remove the DC line noise (baseline drift)
    Wn = fc/(fs/2) is the cutoff frequency, frequency at which we lose 3dB.
    For digital filters, Wn is normalized from 0 to 1, where 1 is the Nyquist frequency, pi radians/sample. (Wn is thus in half-cycles / sample.)
    '''
    b, a = signal.butter(4, (2.0 / (fs_hz / 2.0), 44.0 / (fs_hz / 2.0)), btype='bandpass')
    f_data = signal.lfilter(b, a, data, axis=0)

    # OTHER FILTERS

    # filter the data to remove DC
    # hp_cutoff_hz = 1.0
    # b1, a1 = signal.butter(2, hp_cutoff_hz / (fs_hz / 2.0), 'highpass')  # define the filter
    # ff_data = signal.lfilter(b1, a1, data, 0)  # apply along the zeroeth dimension

    # notch filter the data to remove 50 Hz and 100 Hz
    # notch_freq_hz = np.array([50.0])  # these are the center frequencies
    # for freq_hz in np.nditer(notch_freq_hz):  # loop over each center freq
    #     bp_stop_hz = freq_hz + 3.0 * np.array([-1, 1])  # set the stop band
    #     b, a = signal.butter(3, bp_stop_hz / (fs_hz / 2.0), 'bandstop')  # create the filter
    #     fff_data = signal.lfilter(b, a, f_data, 0)  # apply along the zeroeth dimension

    return f_data

def extract_freqbandmean(N, fe, signal, fmin, fmax):
    #f = np.linspace(0,fe/2,int(np.floor(N/2)))
    fftsig = abs(np.fft.fft(signal))
    # print fftsig.shape
    fftsig = fftsig[fmin:fmax]
    mean = np.mean(fftsig)
    return mean

def enqueue_output(out, queue):
    while True:
        lines = out.readline()
        out.flush()
        #if lines != '\n' && lines.isDigit():
        if lines != '\n' :
            queue.put(lines[:-1])
        