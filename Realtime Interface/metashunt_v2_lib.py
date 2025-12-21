import serial
import time 
import struct 
import array
import serial.tools.list_ports
import json
import math
import numpy as np

config_index_dict = {
    "R19" : 0,
    "R17" : 1,
    "R15" : 2,
    "R13" : 3,
    "R11" : 4,
    "R9" : 5,
    "R2" : 6,
    "R1" : 7,
    "R_FET" : 8
}

class MEASUREMENT:
    def __init__(self, time, current_ma):
        self.time = time 
        self.current_ma = current_ma 

class MetaShuntV2:
    def __init__(self):
        self.ser = None
        self.measurements = []

    def get_packet(self, timeout):
        step = 0
        count = 0
        chk = 0
        payload = []
        start_time = time.time()

        while time.time() < start_time + timeout:
            try:
                data = self.ser.read(1)
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
                    print("MetaShunt V2 checksum wrong. Should be {0}, was {1}".format(chk, data))
                    print("Payload: ")
                    print(payload)
                    step = 0
                    count = 0
                    payload = []

    def get_config_request_response(self, timeout):
        step = 0
        count = 0
        chk = 0
        payload = []
        start_time = time.time()

        while time.time() < start_time + timeout:
            try:
                data = self.ser.read(1)
            except TypeError:
                return None
            if data:
                data = ord(data)

            if(step == 0 and data == 0xAA):
                step += 1
                chk = 0
            elif(step == 1 and data == 0x04):
                step += 1
                chk += data
                chk &= 0xFF
                payload = []
                count = 0
            elif(step == 1 and data != 0x04):
                # Not a correct message, so reset
                step = 0
            elif(step == 2):
                if(count < 5):
                    payload.append(data)
                    count += 1
                    chk += data
                    chk &= 0xFF
                    if count == 5:
                        step += 1
            elif(step == 3):
                if(data == chk):
                    return payload
                else:
                    step = 0
                    count = 0
    
    def send_config(self, index, data):
        payload = bytearray(struct.pack("<BBBBf",0xAA,2,5,index,data))
        chk = 0
        for i in range(1,len(payload)):
            chk += payload[i]
            chk &= 0xFF
        payload.append(chk)
        self.ser.write(bytearray(payload))

    def request_config(self, index):
        payload = bytearray(struct.pack("<BBBB",0xAA,3,1,index))
        chk = 0
        for i in range(1,len(payload)):
            chk += payload[i]
            chk &= 0xFF
        payload.append(chk)
        self.ser.reset_input_buffer()
        self.ser.write(bytearray(payload))
        self.ser.reset_input_buffer()
    
    def connect(self):
        # Figure out the correct port
        port = ""
        connected = [comport for comport in serial.tools.list_ports.comports()]

        for comport in connected:
            if comport.vid == 1155 and comport.pid == 22336:
                port = comport[0]
                break

        if port != "":
            self.ser = serial.Serial(port, timeout=0.1)  # open serial port
            self.ser.reset_input_buffer()
            print("Connected to MetaShunt V2")
            return True
        else:
            print("Could not connect to MetaShunt V2")
            return False
        
    def measure(self, run_time):
        start_time = time.time()
        self.ser.reset_input_buffer()
        while self.ser.in_waiting > 0:
            self.ser.read(self.ser.in_waiting)

        # Record data
        while(time.time() < start_time + run_time):
            # get payload
            payload = self.get_packet(timeout=0.1)
            if payload:
                # unpack it
                line_spec = "<If"
                info = struct.unpack(line_spec, array.array('B',payload).tobytes())
                self.measurements.append(MEASUREMENT(time=info[0],current_ma=info[1]))
    
    def clear_measurements(self):
        self.ser.reset_input_buffer()
        self.measurements = []

    def get_measurements(self):
        current_ma = np.array([ms.current_ma for ms in self.measurements])
        return current_ma
    
    def measurement_stats(self):
        num_measurements = len(self.measurements)
        measurement_mean_ma = None
        measurement_std_dev_ma = None
        if num_measurements > 0:
            current_ma = self.get_measurements()
            measurement_mean_ma = np.mean(current_ma)
            measurement_std_dev_ma = np.std(current_ma)
        return (num_measurements, measurement_mean_ma, measurement_std_dev_ma)
    
    def disconnect(self):
        self.ser.close()

    def configure(self, config_file_name):
        f = open(config_file_name)

        config_data = json.load(f)

        status = True

        for key in config_data:
            time.sleep(0.1)
            # Send data
            print("Setting resistor {0} to {1} Ohm".format(key, config_data[key]))
            self.send_config(config_index_dict[key], config_data[key])
            time.sleep(0.1)
            self.request_config(config_index_dict[key])
            payload = self.get_config_request_response(timeout=0.15)
            if payload:
                # unpack it
                line_spec = "<Bf"
                info = struct.unpack(line_spec, array.array('B',payload).tobytes())
                index = info[0]
                value = info[1]

                if index == config_index_dict[key] and math.isclose(value, config_data[key], rel_tol=1e-5):
                    print("Configuration Set Correctly")
                else:
                    status = False
                    print("Received back {} index and {} Ohm".format(index, value))
                    print("Should be {} index and {} Ohm".format(config_index_dict[key], config_data[key]))
                    print("ERROR Configuration Failed")
            else:
                status = False
                print("ERROR ************** Nothing heard back ************** ERROR")
        return status

    def get_config_param(self, key):
        time.sleep(0.1)
        self.request_config(config_index_dict[key])
        payload = self.get_config_request_response(timeout=0.15)
        value = None
        if payload:
            # unpack it
            line_spec = "<Bf"
            info = struct.unpack(line_spec, array.array('B',payload).tobytes())
            index = info[0]
            value = info[1]
        return value


if __name__ == "__main__":
    this_ms2 = MetaShuntV2()
    this_ms2.connect()

    this_ms2.measure(4.0)
    (num_meas, avg_ma, std_dev_ma) = this_ms2.measurement_stats()
    print("MetaShunt V2 Average Current {0:.4f} mA".format(avg_ma))
