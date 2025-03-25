import serial
import struct 
import array
import sys 
import time
import serial.tools.list_ports
import json
import math

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

    if(len(sys.argv) > 1):
        config_file_name = sys.argv[1]

        f = open(config_file_name)

        config_data = json.load(f)

        for key in config_data:
            time.sleep(0.1)
            # Send data
            print("Setting resistor {0} to {1} Ohm".format(key, config_data[key]))

            payload = bytearray(struct.pack("<BBBBf",0xAA,2,5,config_index_dict[key],config_data[key]))
            chk = 0
            for i in range(1,len(payload)):
                chk += payload[i]
                chk &= 0xFF
            payload.append(chk)
            ser.write(bytearray(payload))

            time.sleep(0.1)
            # Request data
            payload = bytearray(struct.pack("<BBBB",0xAA,3,1,config_index_dict[key]))
            chk = 0
            for i in range(1,len(payload)):
                chk += payload[i]
                chk &= 0xFF
            payload.append(chk)
            ser.reset_input_buffer()
            ser.write(bytearray(payload))
            ser.reset_input_buffer()

            # Get the response
            payload = get_packet(ser, time.time(), 0.15)
            if payload:
                # unpack it
                line_spec = "<Bf"
                info = struct.unpack(line_spec, array.array('B',payload).tobytes())
                index = info[0]
                value = info[1]

                if index == config_index_dict[key] and math.isclose(value, config_data[key], rel_tol=1e-5):
                    print("Configuration Set Correctly")
                else:
                    print("Received back {} index and {} Ohm".format(index, value))
                    print("Should be {} index and {} Ohm".format(config_index_dict[key], config_data[key]))
                    print("Configuration Failed")
            else:
                print("ERROR ************** Nothing heard back ************** ERROR")


        f.close()

    else:
        print("Please provide a config file")
        exit()