# metashunt_interface
Tools for interfacing with the MetaShunt power profiling tool

For realtime measurements (recording data and showing plots of the data), see the "metashunt_realtime_interface.py" Python script in the Realtime Interface folder.
To use, follow these rules:

python metashunt_realtime_interface.py h --- Provides helpful information

python metashunt_realtime_interface.py s [measurement_time_seconds] --- Get streaming data, by default for 10 seconds

python metashunt_realtime_interface.py b rate_hz --- Burst reads 32,000 samples immediately

python metashunt_realtime_interface.py b rate_hz r current_level_uA --- Burst reads 32,000 samples once current rises over the specified level

python metashunt_realtime_interface.py b rate_hz f current_level_uA --- Burst reads 32,000 samples once current falls below the specified level

python metashunt_realtime_interface.py b rate_hz s stage_index --- Burst reads 32,000 samples once system operates at specified stage index

Note: Burst measurements are recorded at up to 25.5kHz
