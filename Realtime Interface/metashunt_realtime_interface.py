import serial
import time 
import struct 
import array
import sys 
import serial.tools.list_ports
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

class MEASUREMENT:
    def __init__(self, time, current_ma):
        self.time = time 
        self.current_ma = current_ma 

def get_packet(ser, start_time, timeout):
    step = 0
    count = 0
    chk = 0
    payload = []

    while time.time() < start_time + timeout:
        try:
            data = ser.read(1)
        except TypeError:
            return None
        if data:
            data = ord(data)

        if(step == 0 and data == 0xAA):
            step += 1
        elif(step == 1):
            if(count < 8):
                payload.append(data)
                count += 1
                chk += data
                chk &= 0xFF
                if count == 8:
                    step += 1
        elif(step == 2):
            if(data == chk):
                return payload
            else:
                print("Checksum wrong")
                step = 0
                count = 0

def display_how_to_use():
    print("To use, follow these rules:")
    print("python metashunt_realtime_interface.py h --- Provides helpful information")
    print("python metashunt_realtime_interface.py s [measurement_time_seconds] --- Get streaming data, by default for 10 seconds")
    print("python metashunt_realtime_interface.py l [measurement_time_seconds] [CSV_file_name] --- Log streaming data, by default for 10 seconds")
    print("Note: Burst measurements up to 25.5kHz")
    print("python metashunt_realtime_interface.py b rate_hz --- Burst reads 32,000 samples immediately")
    print("python metashunt_realtime_interface.py b rate_hz r current_level_uA --- Burst reads 32,000 samples once current rises over the specified level")
    print("python metashunt_realtime_interface.py b rate_hz f current_level_uA --- Burst reads 32,000 samples once current falls below the specified level")
    print("python metashunt_realtime_interface.py b rate_hz s stage_index --- Burst reads 32,000 samples once system operates at specified stage index")
    print("python metashunt_realtime_interface.py b rate_hz i --- Burst reads 32,000 samples once input IO rises. NOT SUPPORTED YET")

if __name__ == "__main__":

    # Figure out the correct port
    port = ""
    connected = [comport for comport in serial.tools.list_ports.comports()]

    for comport in connected:
        if "STM" in comport[1]:
            port = comport[0]
            break

    if port != "":
        ser = serial.Serial(port, timeout=0.1)  # open serial port
        print("Connected to MetaShunt")
    else:
        print("Could not connect to MetaShunt")
        sys.exit()
    

    measurements = []

    start_time = time.time()
    run_time = None
    trig_type = None
    burst_rate = 1000
    trigger_level = 0
    trigger_id = 0
    rate_100s_hz = 10
    burst_number_measurements = 32000

    if(len(sys.argv) > 1):
        command_character = sys.argv[1]
        if command_character == 's' or command_character == 'l':
            print("Streaming data")
            if len(sys.argv) > 2:
                run_time = float(sys.argv[2])
            else:
                run_time = 10.0

            # Record data
            while(time.time() < start_time + run_time):
                # get payload
                payload = get_packet(ser, time.time(), 0.1)
                if payload:
                    # unpack it
                    line_spec = "<If"
                    info = struct.unpack(line_spec, array.array('B',payload).tobytes())
                    measurements.append(MEASUREMENT(time=info[0],current_ma=info[1]))
        elif command_character == 'b':
            command_burst = 1
            print("Burst read")
            if len(sys.argv) == 3:
                rate_100s_hz = int(round(float(sys.argv[2]) / 100.0))
                trigger_id = 0
            elif len(sys.argv)== 5:
                rate_100s_hz = int(round(float(sys.argv[2]) / 100.0))
                trig_type = sys.argv[3]
                if trig_type == 'r':
                    print("Current rising")
                    trigger_id = 1
                    trigger_ua = float(sys.argv[4])
                    trigger_level = int(round(trigger_ua/5.0))
                elif trig_type == 'f':
                    print("Current falling")
                    trigger_id = 2
                    trigger_ua = float(sys.argv[4])
                    trigger_level = int(round(trigger_ua/5.0))
                elif trig_type == 's':
                    print("Stage level")
                    trigger_id = 3
                    trigger_level = int(sys.argv[4])
                elif trig_type == 'i':
                    print("Input trigger selected. This will be added in the future.")
                    trigger_id = 4
                    exit()
            else:
                print("With burst read, please provide a trigger type and rate")
                display_how_to_use()
                exit()

            if rate_100s_hz > 255:
                print("Burst rate must be less than 25.5kHz")
                exit()

            # Assemble command and send
            payload = [0xAA,command_burst,4,rate_100s_hz,trigger_id,((trigger_level & 0xFF00) >> 8),(trigger_level & 0x00FF )]

            chk = 0
            for i in range(1,len(payload)):
                chk += payload[i]
                chk &= 0xFF
            payload.append(chk)
            ser.write(bytearray(payload))

            time.sleep(0.1)

            # Get the data
            data_received = 0
            while(data_received < burst_number_measurements):
                # get payload
                payload = get_packet(ser, time.time(), 0.1)
                if payload:
                    # unpack it
                    line_spec = "<If"
                    info = struct.unpack(line_spec, array.array('B',payload).tobytes())
                    measurements.append(MEASUREMENT(time=info[0],current_ma=info[1]))
                    data_received = data_received + 1
        elif command_character == 'h':
            display_how_to_use()
            exit()
    else:
        print("Incorrect inputs. Please follow the instructions below.")
        print("..........")
        display_how_to_use()
        exit()

    ser.close()

    print("Readings complete")
    print("Readings received: {}".format(len(measurements)))

    times = np.array([m.time for m in measurements])
    times = times - times[0]
    times_s = times / 1.0e6

    current_ma = np.array([m.current_ma for m in measurements])
    current_ua = np.array([m.current_ma * 1000.0 for m in measurements])

    print("Mean current: {}uA ".format(np.mean(current_ua)))

    if command_character == 'l':
        if len(sys.argv) > 3:
            csv_filename = sys.argv[3]
            csv_output = np.transpose(np.array([times, current_ua]))
            np.savetxt(csv_filename, csv_output, header='time [us], current [uA]')
        else:
            print("Please provide a CSV file name")
            display_how_to_use()
            exit()

    fig, ax = plt.subplots()
    ax.plot(times_s, current_ua, '.-',label='Current')
    ax.set(xlabel='Time, s', ylabel='Current, uA')
    ax.legend()
    ax.grid()

    fig, axma = plt.subplots()
    axma.plot(times_s, current_ma, '.-',label='Current')
    axma.set(xlabel='Time, s', ylabel='Current, mA')
    axma.legend()
    axma.grid()

    fig, axtm = plt.subplots()
    axtm.plot(np.diff(times), '.-',label='Period')
    axtm.set(xlabel='Sample Index', ylabel='Period, us')
    axtm.legend()
    axtm.grid()

    fig, axfreq = plt.subplots()
    axfreq.plot(np.divide(1.0,np.diff(times_s)), '.-',label='Frequency')
    axfreq.set(xlabel='Sample Index', ylabel='Frequency, Hz')
    axfreq.legend()
    axfreq.grid()

    plt.show()