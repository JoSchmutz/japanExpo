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
    b, a = signal.butter(4, (1.0 / (fs_hz / 2.0), 44.0 / (fs_hz / 2.0)), btype='bandpass')
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

def wave_amplitude(data, fs_hz, NFFT, overlap, buffersize, wave_range):

    # print len(data)
    data = np.asarray(data)
    # print len(data)
    data = data[:, :buffersize]
    # print data.shape #should be (4, 200)

    f_eeg_data = filter_data(data, fs_hz)
    # print f_eeg_data.shape # should be (4, 200)

    #t0 = time.time()
    if wave_range == 'alpha':
        wave_band_Hz = np.array([8, 12])
    elif wave_range == 'gamma':
        wave_band_Hz = np.array([25, 50])
    elif wave_range == 'beta':
        wave_band_Hz = np.array([12, 25])
    elif wave_range == 'theta':
        wave_band_Hz = np.array([4, 7])

    size = f_eeg_data.shape[0] # should be 4
    # print "filtered data number of channels " + size

    mean_range = np.zeros((size, 1))
    max_range = np.zeros((size,1 ))
    min_range = np.zeros((size, 1))
    ratio = np.zeros((size, 1))

    for channel in range(size):

        # data[channel] = rolling_mean(data[channel])
        # data[channel] = data[channel] - np.mean(data[channel])
        # print(f_eeg_data.shape)

        '''
        NFFT is 200
        We dont care of overlap since we do the spectrogram for only 1 sample.
        The amplitudes of spec_PSDperHz are around 1e-20, why is it so low ?
        There are two columns of spec_PSDperHz, where I should have only one
        '''

        # spec_PSDperHz, freqs, t_spec = mlab.specgram(f_eeg_data[:, channel],
        #                                              NFFT=NFFT,
        #                                              Fs=fs_hz,
        #                                              window=mlab.window_none(),
        #                                              noverlap=overlap)
        #

        amplitutdes = np.fft.fft(f_eeg_data[:, channel])


        print spec_PSDperHz
        # convert the units of the spectral data
        spec_PSDperBin = spec_PSDperHz * fs_hz / float(NFFT)  # convert to "Power Spectral Density per bin"
        spec_PSDperBin = np.asarray(spec_PSDperBin)
        # print(spec_PSDperBin.shape) # from 1 to 110 Hz, step of 1Hz

        # take the average spectrum according to the time - axis 1

        bool_inds_wave_range = (freqs > wave_band_Hz[0]) & (freqs < wave_band_Hz[1])
        #freq_range = freqs[bool_inds_wave_range == 1]
        #freq_range = freq_range[max_range_idx]

        spec_PSDperBin_range = spec_PSDperBin[bool_inds_wave_range]

        mean_range[0][channel] = np.mean(spec_PSDperBin_range)

        max_range[0][channel] = np.amax(spec_PSDperBin_range)

        # get the frequency of the max in each range alpha, beta, theta, gamma
        # max_range_idx = np.argmax(spec_PSDperBin_range)
        # print(freq_alpha, freq_beta, freq_theta, freq_gamma)

    '''
    Get the median, max and min of the 4 channels
    '''

    # print(max_beta)
    med_range = np.median(mean_range[0][:])

    max_range = np.amax(mean_range[0][:])

    min_range = np.min(mean_range[0][:])

    # ratio = med_beta / med_theta
    # time_last_event = time.time()-t0

    # return [med_alpha, max_alpha, min_alpha, freq_alpha,
    #        med_beta, max_beta, min_beta, freq_beta,
    #        med_theta, max_theta, min_theta, freq_theta,
    #        med_gamma, max_gamma, min_gamma, freq_gamma, time_last_alpha]

    results = [med_range, max_range, min_range]
    result = results
    # print(med_gamma.type())

    return result

def enqueue_output(out, queue):
    while True:
        lines = out.readline()
        out.flush()
        queue.put(lines)

def sine_tone(freq, duration, bitrate):
    #See http://en.wikipedia.org/wiki/Bit_rate#Audio
    BITRATE = bitrate #number of frames per second/frameset.

    #See http://www.phy.mtu.edu/~suits/notefreqs.html
    FREQUENCY = freq #Hz, waves per second, 261.63=C4-note.
    LENGTH = duration #seconds to play sound

    NUMBEROFFRAMES = int(BITRATE * LENGTH)
    RESTFRAMES = NUMBEROFFRAMES % BITRATE
    WAVEDATA = ''
    # print (type(FREQUENCY))

    for x in xrange(NUMBEROFFRAMES):
        WAVEDATA += chr(int(math.sin(x / ((BITRATE / FREQUENCY) / math.pi)) * 127 + 128))
    #fill remainder of frameset with silence
    for x in xrange(RESTFRAMES):
        WAVEDATA += chr(128)

    p = PyAudio()
    stream = p.open(
        format=p.get_format_from_width(1),
        channels=1,
        rate=BITRATE,
        output=True,
        )
    stream.write(WAVEDATA)
    stream.stop_stream()
    stream.close()
    p.terminate()
