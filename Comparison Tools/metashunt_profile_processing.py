import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from enum import Enum
from scipy.signal import correlate, correlation_lags

def estimate_time_offset(time_1, current_1, time_2, current_2):
    # Create a common time base where both signals have valid data
    start = max(min(time_1), min(time_2))
    end = min(max(time_1), max(time_2))
    if end <= start:
        raise ValueError("No overlapping time range between measured and imported data")

    # Uniform time steps for interpolation
    num_points = 10000
    common_time = np.linspace(start, end, num_points)

    # Interpolate both signals onto the common time base
    sig_1_interp = np.interp(common_time, time_1, current_1)
    sig_2_interp = np.interp(common_time, time_2, current_2)

    # Remove mean to center signals
    sig_1_zero_mean = sig_1_interp - np.mean(sig_1_interp)
    sig_2_zero_mean = sig_2_interp - np.mean(sig_2_interp)

    # Cross-correlate the two signals
    corr = correlate(sig_1_zero_mean, sig_2_zero_mean, mode='full')
    lags = correlation_lags(len(sig_1_zero_mean), len(sig_2_zero_mean), mode='full')
    
    # Find the lag with maximum correlation
    best_lag = lags[np.argmax(corr)]

    # Convert lag to time offset
    dt = (common_time[-1] - common_time[0]) / (num_points - 1)
    time_offset = best_lag * dt

    return time_offset


class FILETYPE(Enum):
    METASHUNT_LOG = 1
    EMBEDDED_POWER_MODEL = 2
    OTII_LOG = 3
    PPK2_LOG = 4

class ALIGNMENTTYPE(Enum):
    TIMESHIFT = 1
    CROSSCORRELATE = 2
    NOALIGN = 3

class PROFILE:
    def __init__(self, filename: str, filetype: FILETYPE, alignment_type: ALIGNMENTTYPE, label: str, t_shift: float = None, alignment_profile = None, voltage: float = 3.3):
        self.filename = filename
        self.filetype = filetype
        self.alignment_type = alignment_type
        self.label = label
        self.t_shift = t_shift
        self.current_ua = []
        self.power_mW = []
        self.energy_mWh = []
        self.t_s = []
        self.num_datapoints = None
        self.voltage = voltage

        # Load the data
        if filetype == FILETYPE.METASHUNT_LOG:
            data = np.loadtxt(filename, delimiter=",", skiprows=1)
            self.t_s = data[:,0]
            self.t_s = self.t_s - self.t_s[0]
            self.current_ua = data[:,1] * 1.0e3
            self.num_datapoints = len(self.t_s)
        elif filetype == FILETYPE.OTII_LOG:
            data = np.loadtxt(filename, delimiter=",", skiprows=1)
            self.t_s = data[:,0]
            self.current_ua = data[:,1] * 1.0e6
            self.num_datapoints = len(self.t_s)
        elif filetype == FILETYPE.EMBEDDED_POWER_MODEL:
            data = np.loadtxt(filename, delimiter=",", skiprows=1)
            self.t_s = data[:,0]
            self.current_ua = data[:,1] * 1.0e3
            self.num_datapoints = len(self.t_s)
        elif filetype == FILETYPE.PPK2_LOG:
            data = np.loadtxt(filename, delimiter=",", skiprows=1)
            self.t_s = data[:,0] * 0.001
            self.current_ua = data[:,1]
            self.num_datapoints = len(self.t_s)

        if alignment_type == ALIGNMENTTYPE.NOALIGN:
            pass
        elif alignment_type == ALIGNMENTTYPE.TIMESHIFT:
            self.t_s = self.t_s + t_shift
        elif alignment_type == ALIGNMENTTYPE.CROSSCORRELATE:

            best_offset_t = estimate_time_offset(self.t_s, self.current_ua, alignment_profile.t_s, alignment_profile.current_ua)
            print("Best time offset by cross-correlation is {}s".format(best_offset_t))
            self.t_s = self.t_s - best_offset_t

        # Calculate power and cumulative energy
        self.power_mW = 0.001 * self.voltage * self.current_ua
        self.energy_mWh = np.zeros((len(self.power_mW)))
        for i in range(1,len(self.power_mW)):
            self.energy_mWh[i] = self.energy_mWh[i-1] + (self.power_mW[i] + self.power_mW[i-1])*0.5*(self.t_s[i] - self.t_s[i-1])/3600.0

def plot_profiles(profiles_array, t_lim=None, log_plots=False):

    fig, ax = plt.subplots()
    for profile in profiles_array:

        ax.plot(profile.t_s, profile.current_ua, label=profile.label)

    ax.set(xlabel='Time, s', ylabel='Current, uA',
        title='Current Profile Comparison')
    if t_lim is not None:
        ax.set(xlim=t_lim)
    ax.grid()
    ax.legend()

    fig, ax = plt.subplots()
    for profile in profiles_array:

        ax.plot(profile.t_s, profile.power_mW, label=profile.label)

    ax.set(xlabel='Time, s', ylabel='Power, mW',
        title='Power Profile Comparison')
    if t_lim is not None:
        ax.set(xlim=t_lim)
    ax.grid()
    ax.legend()

    fig, ax = plt.subplots()
    for profile in profiles_array:

        ax.plot(profile.t_s, profile.energy_mWh, label=profile.label)

    ax.set(xlabel='Time, s', ylabel='Energy, mWh',
        title='Cumulative Energy Profile Comparison')
    if t_lim is not None:
        ax.set(xlim=t_lim)
    ax.grid()
    ax.legend()

    if log_plots:
        fig, ax = plt.subplots()
        for profile in profiles_array:

            ax.semilogy(profile.t_s, profile.current_ua, label=profile.label)

        ax.set(xlabel='Time, s', ylabel='Current, uA',
            title='Current Profile Comparison, Logarithmic')
        if t_lim is not None:
            ax.set(xlim=t_lim)
        ax.grid()
        ax.legend()

        fig, ax = plt.subplots()
        for profile in profiles_array:

            ax.semilogy(profile.t_s, profile.energy_mWh, label=profile.label)

        ax.set(xlabel='Time, s', ylabel='Energy, mWh',
            title='Cumulative Energy Profile Comparison, Logarithmic')
        if t_lim is not None:
            ax.set(xlim=t_lim)
        ax.grid()
        ax.legend()

    plt.show()