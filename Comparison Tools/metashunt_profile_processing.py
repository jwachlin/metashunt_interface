import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from enum import Enum
from scipy import signal


class FILETYPE(Enum):
    METASHUNT_LOG = 1
    EMBEDDED_POWER_MODEL = 2
    OTII_LOG = 3

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
            time_us = data[:,0]
            self.t_s = time_us * 1.0e-6
            self.t_s = self.t_s - self.t_s[0]
            self.current_ua = data[:,1]
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

        if alignment_type == ALIGNMENTTYPE.NOALIGN:
            pass
        elif alignment_type == ALIGNMENTTYPE.TIMESHIFT:
            self.t_s = self.t_s + t_shift
        elif alignment_type == ALIGNMENTTYPE.CROSSCORRELATE:

            # Calculate the cross-correlation
            correlation = signal.correlate(self.current_ua, alignment_profile.current_ua, mode='valid')

            # Find the lag that maximizes the cross-correlation
            lag = np.argmax(correlation)

            # Apply the timeshift
            self.t_s = self.t_s - self.t_s[lag]

        # Calculate power and cumulative energy
        self.power_mW = 0.001 * self.voltage * self.current_ua
        self.energy_mWh = np.zeros((len(self.power_mW)))
        for i in range(1,len(self.power_mW)):
            self.energy_mWh[i] = self.energy_mWh[i-1] + (self.power_mW[i] + self.power_mW[i-1])*0.5*(self.t_s[i] - self.t_s[i-1])/3600.0

def plot_profiles(profiles_array):

    fig, ax = plt.subplots()
    for profile in profiles_array:

        ax.plot(profile.t_s, profile.current_ua, label=profile.label)

    ax.set(xlabel='Time, s', ylabel='Current, uA',
        title='Current Profile Comparison')
    ax.grid()
    ax.legend()

    fig, ax = plt.subplots()
    for profile in profiles_array:

        ax.plot(profile.t_s, profile.power_mW, label=profile.label)

    ax.set(xlabel='Time, s', ylabel='Power, mW',
        title='Power Profile Comparison')
    ax.grid()
    ax.legend()

    fig, ax = plt.subplots()
    for profile in profiles_array:

        ax.plot(profile.t_s, profile.energy_mWh, label=profile.label)

    ax.set(xlabel='Time, s', ylabel='Energy, mWh',
        title='Cumulative Energy Profile Comparison')
    ax.grid()
    ax.legend()

    plt.show()