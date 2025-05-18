# metashunt_interface
Tools for interfacing with the MetaShunt power profiling tool

Two versions of MetaShunt hardware are supported. For V2 MetaShunt, use scripts with "_v2_" in the title. Or, use the GUI.

For version 1 of MetaShunt:

For realtime measurements (recording data and showing plots of the data), see the "metashunt_realtime_interface.py" Python script in the Realtime Interface folder.
To use, follow these rules:

python metashunt_realtime_interface.py h --- Provides helpful information
python metashunt_realtime_interface.py s [measurement_time_seconds] --- Get streaming data, by default for 10 seconds
python metashunt_realtime_interface.py b rate_hz --- Burst reads 32,000 samples immediately
python metashunt_realtime_interface.py b rate_hz r current_level_uA --- Burst reads 32,000 samples once current rises over the specified level
python metashunt_realtime_interface.py b rate_hz f current_level_uA --- Burst reads 32,000 samples once current falls below the specified level
python metashunt_realtime_interface.py b rate_hz s stage_index --- Burst reads 32,000 samples once system operates at specified stage index
Note: Burst measurements are recorded at up to 25.5kHz

For version 2 of MetaShunt:
For realtime measurements (recording data and showing plots of the data), see the "metashunt_v2_realtime_interface.py" Python script in the Realtime Interface folder.
To use, follow these rules:

python metashunt_realtime_v2_interface.py h --- Provides helpful information
python metashunt_realtime_v2_interface.py s [measurement_time_seconds] --- Get streaming data, by default for 10 seconds
python metashunt_realtime_v2_interface.py l [measurement_time_seconds] [CSV_file_name] --- Log streaming data, by default for 10 seconds
Note: Burst measurements up to 127.5kHz
python metashunt_realtime_v2_interface.py b rate_hz --- Burst reads 37,500 samples immediately
python metashunt_realtime_v2_interface.py b rate_hz r current_level_uA --- Burst reads 37,500 samples once current rises over the specified level
python metashunt_realtime_v2_interface.py b rate_hz f current_level_uA --- Burst reads 37,500 samples once current falls below the specified level
python metashunt_realtime_v2_interface.py b rate_hz s stage_index --- Burst reads 37,500 samples once system operates at specified stage index
python metashunt_realtime_v2_interface.py b rate_hz i --- Burst reads 37,500 samples once KEY2 button is pressed

Or, run the "metashunt_v2_gui.py" interface from the GUI folder.
