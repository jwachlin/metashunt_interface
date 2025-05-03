from PIL import Image
import dearpygui.dearpygui as dpg
import threading
import serial
import serial.tools.list_ports
import struct
import array
import time
import io
import numpy as np
from scipy.signal import correlate, correlation_lags

# Measurement buffer
measured_times_raw = []
measured_currents_uA = []

# Imported data
imported_times_sec = []
imported_currents_uA = []
time_offset = 0.0  # For aligning imported data
charge_offset_uAh = 0.0
imported_charge_offset_uAh = 0.0

# Plot handles
current_plot_series = "current_series"
charge_plot_series = "charge_series"

# Protect data
data_lock = threading.Lock()

# Serial
ser = None
running = False
is_burst = False
burst_rate_hz = 50000
trigger_type = 0
trigger_level = 1000

# Desired logo display size
LOGO_DISPLAY_WIDTH = 300
LOGO_DISPLAY_HEIGHT = 69

# Load and resize image using Pillow
image = Image.open("metashuntLogo.png").convert("RGBA")
image = image.resize((LOGO_DISPLAY_WIDTH, LOGO_DISPLAY_HEIGHT), Image.Resampling.LANCZOS)

# Flatten image data and normalize to 0.0–1.0 for DPG
pixels = list(image.getdata())
flat_pixels = [c / 255.0 for pixel in pixels for c in pixel]

def find_metashunt_port():
    for comport in serial.tools.list_ports.comports():
        if "STM" in comport.description:
            return comport.device
    return None

def get_packet(ser, timeout=0.1):
    step, count, chk = 0, 0, 0
    payload = []
    start_time = time.time()
    while time.time() < start_time + timeout:
        try:
            byte = ser.read(1)
            if byte:
                data = ord(byte)
                if step == 0 and data == 0xAA:
                    step = 1
                    count, chk, payload = 0, 0, []
                elif step == 1:
                    payload.append(data)
                    count += 1
                    chk = (chk + data) & 0xFF
                    if count == 8:
                        step = 2
                elif step == 2:
                    if data == chk:
                        return payload
                    else:
                        print("Checksum on receive failed")
                        step, count, payload = 0, 0, []
        except:
            return None
    return None

def serial_worker():
    global running, ser, measured_times_raw, measured_currents_uA, is_burst, burst_rate_hz, trigger_type, trigger_level
    port = find_metashunt_port()
    if not port:
        print("MetaShunt not found.")
        return
    
    first_packet = True
    t_offset_us = 0
    packet_count = 0
    burst_number_measurements = 37500

    ser = serial.Serial(port, timeout=0.1)
    print("Connected to MetaShunt V2 on", port)
    start = time.time()

    # If in burst, send the burst command
    if is_burst:
        print("Starting measurement, burst mode")
        start_burst_reading()

    while running:
        packet = get_packet(ser, timeout=0.5)
        if packet:
            line_spec = "<If"
            info = struct.unpack(line_spec, array.array('B', packet).tobytes())
            t_us = info[0] / 4.0
            i_ma = info[1]
            if first_packet:
                first_packet = False
                t_offset_us = t_us
            t_us = t_us - t_offset_us

            with data_lock:
                measured_times_raw.append(t_us)
                measured_currents_uA.append(i_ma * 1000.0)

            packet_count = packet_count + 1
            if is_burst:
                if packet_count == burst_number_measurements:
                    stop_measurement()
        else:
            print("No packet received in time at {}".format(time.time()))

# Function to handle burst reading
def start_burst_reading():
    global ser, burst_rate_hz, trigger_level, trigger_type
    command_burst = 1
    rate_500s_hz = int(round(float(burst_rate_hz) / 500.0))
    payload = [0xAA, command_burst, 4, rate_500s_hz, trigger_type, (trigger_level >> 8) & 0xFF, trigger_level & 0xFF]
    
    # Calculate checksum
    chk = sum(payload[1:]) & 0xFF
    payload.append(chk)
    
    # Send the burst read command
    ser.write(bytearray(payload))

    time.sleep(0.1)
    ser.reset_input_buffer()

def update_plots():
    global charge_offset_uAh, imported_charge_offset_uAh

    times_np = []
    current_np = []
    with data_lock:
        times_np = np.array(measured_times_raw)
        current_np = np.array(measured_currents_uA)

    if len(times_np) < 2:
        dpg.set_value(current_plot_series, [[], []])
        dpg.set_value(charge_plot_series, [[], []])
    else:
        times_s = times_np / 1e6  # Convert to seconds
        dt = np.diff(times_s)
        dt = np.append(dt, dt[-1])  # For matching shape
            
        if len(current_np) != len(dt):
            print(f"[WARN] Mismatched lengths: current={len(current_np)}, dt={len(dt)}")
        else:
            charge_uah = (np.cumsum(current_np * dt) / 3600.0)
            charge_uah += charge_offset_uAh

            dpg.set_value(current_plot_series, [times_s.tolist(), current_np.tolist()])
            dpg.set_value(charge_plot_series, [times_s.tolist(), charge_uah.tolist()])

    # Add imported data if available
    if len(imported_times_sec) > 2:
        imported_times_sec_shifted = imported_times_sec + time_offset
        imported_times_sec_shifted_dt = imported_times_sec_shifted[1] - imported_times_sec_shifted[0]
        imported_charge = np.cumsum(imported_currents_uA * np.diff(np.append(imported_times_sec_shifted[0]-imported_times_sec_shifted_dt, imported_times_sec_shifted))) / 3600.0
        imported_charge += imported_charge_offset_uAh

        dpg.set_value(imported_current_plot_series, [imported_times_sec_shifted.tolist(), imported_currents_uA.tolist()])
        dpg.set_value(imported_charge_plot_series, [imported_times_sec_shifted.tolist(), imported_charge.tolist()])
    else:
        dpg.set_value(imported_current_plot_series, [[], []])
        dpg.set_value(imported_charge_plot_series, [[], []])

    if running:
        dpg.fit_axis_data("current_x_axis")
        dpg.fit_axis_data("current_y_axis")
        dpg.fit_axis_data("charge_x_axis")
        dpg.fit_axis_data("charge_y_axis")

def export_data_callback():
    if len(measured_times_raw) == 0 or len(measured_currents_uA) == 0:
        print("No data to export.")
        return

    dpg.show_item("file_dialog_id")

def export_data_to_file(sender, app_data):
    if not app_data['file_path_name']:
        print("Export canceled.")
        return

    export_path = app_data['file_path_name']
    
    with data_lock:
        times_s = np.array(measured_times_raw) / 1e6  # Convert to seconds
        current_mA = np.array(measured_currents_uA) / 1000.0  # Convert uA to mA

    try:
        with open(export_path, "w") as f:
            f.write("Time (s),Current (mA)\n")
            for t, i in zip(times_s, current_mA):
                f.write(f"{t:.6f},{i:.8f}\n")
        print(f"Data exported to '{export_path}'")
    except Exception as e:
        print(f"Failed to export data: {e}")


def import_data_from_file(app_data):
    global imported_times_sec, imported_currents_uA

    path = app_data['file_path_name']
    if not path:
        print("Import canceled.")
        return

    try:
        times_list = []
        currents_list = []
        with open(path, "r") as f:
            lines = f.readlines()
            for line in lines[1:]:  # Skip header
                t_str, i_str = line.strip().split(',')
                times_list.append(float(t_str))
                currents_list.append(float(i_str) * 1000.0)  # mA to uA
        imported_times_sec = np.array(times_list)
        imported_currents_uA = np.array(currents_list)
        avg_imported_current = np.mean(imported_currents_uA)

        if len(imported_currents_uA) > 2:
            dpg.set_value("imported_current_series", [imported_times_sec, imported_currents_uA])
            dpg.set_item_label("imported_current_series", f"Imported Current (avg: {avg_imported_current:.2f} uA)")
            dpg.show_item("imported_current_series")
            dpg.show_item("imported_charge_series")

        print(f"Imported {len(imported_times_sec)} points from '{path}'")
        update_plots()

    except Exception as e:
        print(f"Failed to import data: {e}")

def estimate_time_offset(measured_time, measured_current, imported_time, imported_current):
    # Create a common time base where both signals have valid data
    start = max(min(measured_time), min(imported_time))
    end = min(max(measured_time), max(imported_time))
    if end <= start:
        raise ValueError("No overlapping time range between measured and imported data")

    # Uniform time steps for interpolation
    num_points = 5000
    common_time = np.linspace(start, end, num_points)

    # Interpolate both signals onto the common time base
    measured_interp = np.interp(common_time, measured_time, measured_current)
    imported_interp = np.interp(common_time, imported_time, imported_current)

    # Remove mean to center signals
    measured_zero_mean = measured_interp - np.mean(measured_interp)
    imported_zero_mean = imported_interp - np.mean(imported_interp)

    # Cross-correlate the two signals
    corr = correlate(measured_zero_mean, imported_zero_mean, mode='full')
    lags = correlation_lags(len(measured_zero_mean), len(imported_zero_mean), mode='full')
    
    # Find the lag with maximum correlation
    best_lag = lags[np.argmax(corr)]

    # Convert lag to time offset
    dt = (common_time[-1] - common_time[0]) / (num_points - 1)
    time_offset = best_lag * dt

    return time_offset

def update_time_offset(val):
    global time_offset
    time_offset = val
    update_plots()

def align_charge_plot_callback():
    global time_offset, measured_times_raw, measured_currents_uA, imported_times_sec, imported_currents_uA, charge_offset_uAh, imported_charge_offset_uAh
    if len(measured_times_raw) < 2 or len(imported_times_sec) < 2 or time_offset == 0.0:
        # Do nothing, nothing to align
        return
    
    times_np = []
    current_np = []
    with data_lock:
        times_np = np.array(measured_times_raw)
        current_np = np.array(measured_currents_uA)
    times_s = times_np / 1e6  # Convert to seconds

    # Assume we have manually aligned these. The charge level of imported data then will be at zero somewhere
    # not at t = 0. time_offset is added to imported data
    if time_offset > 0.0:
        # This implies that imported measurements have been shifted forward in time.
        # We want to find the index in times where it crosses the t=0 axis, then lower
        # all charge measurements by the corresponding amount
        temp_t = imported_times_sec + time_offset
        idx = np.searchsorted(times_s, temp_t[0]) # Imported time in seconds already
        dt = np.diff(times_s)
        dt = np.append(dt, dt[-1])  # For matching shape 
        charge_uah = (np.cumsum(current_np * dt) / 3600.0)
        charge_uah += charge_offset_uAh
        
        charge_offset_uAh = -charge_uah[idx]
    else:
        # This implies that imported measurements have been shifted backwards in time.
        # We want to find the index in imported_times_sec where it crosses the t=0 axis, then lower
        # all charge measurements by the corresponding amount
        idx = np.searchsorted(imported_times_sec+time_offset, times_s[0]) # Imported time in seconds already

        imported_times_sec_shifted = imported_times_sec + time_offset
        imported_times_sec_shifted_dt = imported_times_sec_shifted[1] - imported_times_sec_shifted[0]
        imported_charge = np.cumsum(imported_currents_uA * np.diff(np.append(imported_times_sec_shifted[0]-imported_times_sec_shifted_dt, imported_times_sec_shifted))) / 3600.0
        imported_charge += imported_charge_offset_uAh

        imported_charge_offset_uAh = -imported_charge[idx]
    update_plots()

def auto_align_callback():
    global imported_times_sec, imported_currents_uA, measured_times_raw, measured_currents_uA, time_offset

    times_np = []
    current_np = []
    with data_lock:
        times_np = np.array(measured_times_raw)
        current_np = np.array(measured_currents_uA)
    
    times_s = times_np / 1e6

    if (len(times_s) > 2 and len(current_np) > 2 and len(imported_times_sec) > 2 and len(imported_currents_uA) > 2):
        time_offset = estimate_time_offset(times_s, current_np, imported_times_sec, imported_currents_uA)
        update_plots()

def mode_changed_callback(sender, app_data, user_data):
    global is_burst
    is_burst = (app_data == "Burst")
    dpg.configure_item("burst_config", show=(app_data == "Burst"))
    dpg.configure_item("cont_config", show=(app_data == "Continuous"))

def burst_trigger_changed_callback(sender, app_data, user_data):
    dpg.configure_item("current_trigger_level_config", show=(app_data == "Rise Trigger" or app_data == "Fall Trigger"))

def start_measurement():
    global running, measured_times_raw, measured_currents_uA, is_burst, burst_rate_hz, trigger_type, trigger_level
    running = True

    # Reset label
    dpg.set_item_label("current_series", "Current")

    if dpg.does_item_exist("imported_current_series"):
        dpg.hide_item("imported_current_series")
        dpg.hide_item("imported_charge_series")
        

    # Set the parameters
    if is_burst:
        burst_rate_hz = dpg.get_value("burst_rate_picker")
        print("Burst rate {} Hz".format(burst_rate_hz))
        burst_trigger_requested = dpg.get_value("burst_trigger_picker")
        trigger_level = 0
        if burst_trigger_requested == "Rate Only":
            trigger_type = 0
        elif burst_trigger_requested == "Rise Trigger":
            trigger_type = 1
            current_trigger_requested_ua = dpg.get_value("burst_current_level_trigger_picker")
            trigger_level = int(round(current_trigger_requested_ua/5.0))
        elif burst_trigger_requested == "Fall Trigger":
            trigger_type = 2
            current_trigger_requested_ua = dpg.get_value("burst_current_level_trigger_picker")
            trigger_level = int(round(current_trigger_requested_ua/5.0))
            # TODO add stage trigger support
        elif burst_trigger_requested == "Button Trigger":
            trigger_type = 4
            # Trigger level doesn't matter

    with data_lock:
        measured_times_raw = []
        measured_currents_uA = []
    threading.Thread(target=serial_worker, daemon=True).start()

def stop_measurement():
    global running
    running = False
    if ser:
        ser.close()

    # Compute and display stats
    with data_lock:
        current_np = np.array(measured_currents_uA)
        avg_current = np.mean(current_np)
        dpg.set_item_label("current_series", f"Current (avg: {avg_current:.2f} uA)")

def clear_measurement():
    global measured_times_raw, measured_currents_uA, imported_times_sec, imported_currents_uA
    with data_lock:
        measured_times_raw = []
        measured_currents_uA = []
    imported_times_sec = []
    imported_currents_uA = []
    update_plots()

# GUI Setup
dpg.create_context()

with dpg.window(label="MetaShunt Interface", width=1000, height=800, tag="main_window"):
    dpg.add_text("Mode Selection")
    dpg.add_combo(["Continuous", "Burst"], default_value="Continuous", callback=mode_changed_callback, width=400)

    with dpg.group(tag="cont_config", width=400):
        dpg.add_text("Start and Stop Measurements as Needed")

    with dpg.group(tag="burst_config", width=400, show=False):
        dpg.add_combo(["Rate Only", "Rise Trigger", "Fall Trigger","Button Trigger"], 
                      default_value="Rate Only", label="Trigger Type", tag="burst_trigger_picker", callback=burst_trigger_changed_callback)
        dpg.add_input_float(label="Measurement Frequency (Hz)", default_value=10000.0, tag="burst_rate_picker")
        with dpg.group(tag="current_trigger_level_config", width=400, show=False):
            dpg.add_input_float(label="Trigger Level (uA)", default_value=10000.0, tag="burst_current_level_trigger_picker")

    with dpg.group(horizontal=True):
        dpg.add_button(label="Start Measurement", callback=start_measurement)
        dpg.add_button(label="Stop Measurement", callback=stop_measurement)
        dpg.add_button(label="Clear Data", callback=clear_measurement)
    
    with dpg.group(horizontal=True):
        dpg.add_button(label="Export Data", callback=export_data_callback)
        dpg.add_button(label="Import Data", callback=lambda: dpg.show_item("file_dialog_import"))

    # File dialog widget
    with dpg.file_dialog(
        directory_selector=False,
        show=False,
        callback=export_data_to_file,
        id="file_dialog_id",
        width=700,
        height=400,
        modal=True
    ):
        dpg.add_file_extension(".csv", color=(150, 255, 150, 255))
        dpg.add_file_extension("", color=(255, 255, 255, 255))  # Show all files

    # File dialog for importing data
    with dpg.file_dialog(
        directory_selector=False,
        show=False,
        callback=lambda s, a: import_data_from_file(a),
        id="file_dialog_import",
        width=700,
        height=400,
        modal=True
    ):
        dpg.add_file_extension(".csv", color=(150, 255, 150, 255))
        dpg.add_file_extension("", color=(255, 255, 255, 255))


    # Create texture
    with dpg.texture_registry(show=False):
        dpg.add_static_texture(LOGO_DISPLAY_WIDTH, LOGO_DISPLAY_HEIGHT, flat_pixels, tag="logo_tex")

    # Add it in a corner (top-right)
    with dpg.window(label="", no_title_bar=True, no_resize=True, no_move=True, no_background=True, tag="logo_window", pos=(690, 25)):
        dpg.add_image("logo_tex")
    
    dpg.add_spacer(height=10)

    with dpg.plot(label="Current vs Time", height=225, width=-1):
        dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="current_x_axis")
        dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
        with dpg.plot_axis(dpg.mvYAxis, label="Current (uA)", tag="current_y_axis"):
            current_plot_series = dpg.add_line_series([], [], label="Current", tag="current_series")
            imported_current_plot_series = dpg.add_line_series([], [], label="Imported Current", tag="imported_current_series")

    with dpg.plot(label="Accumulated Charge vs Time", height=225, width=-1):
        dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="charge_x_axis")
        with dpg.plot_axis(dpg.mvYAxis, label="Charge (uAh)", tag="charge_y_axis"):
            charge_plot_series = dpg.add_line_series([], [], label="Charge", tag="charge_series")
            imported_charge_plot_series = dpg.add_line_series([], [], label="Imported Charge", tag="imported_charge_series")

    # Zoom and Auto-Fit Controls
    dpg.add_spacer(height=10)
    dpg.add_text("Plot Controls")

    # Auto-fit buttons
    dpg.add_button(label="Auto-fit Current Plot", callback=lambda: (
        dpg.fit_axis_data("current_x_axis"),
        dpg.fit_axis_data("current_y_axis")
    ))
    dpg.add_button(label="Auto-fit Charge Plot", callback=lambda: (
        dpg.fit_axis_data("charge_x_axis"),
        dpg.fit_axis_data("charge_y_axis")
    ))

    # Manual range controls (optional)
    with dpg.collapsing_header(label="Manual Axis Controls", default_open=False):
        dpg.add_text("Current Plot X Axis")
        dpg.add_input_float(label="Min", default_value=0.0, callback=lambda s, a, u: dpg.set_axis_limits("current_x_axis", a, dpg.get_value("curr_x_max")), tag="curr_x_min")
        dpg.add_input_float(label="Max", default_value=1.0, callback=lambda s, a, u: dpg.set_axis_limits("current_x_axis", dpg.get_value("curr_x_min"), a), tag="curr_x_max")

        dpg.add_text("Current Plot Y Axis")
        dpg.add_input_float(label="Min", default_value=0.0, callback=lambda s, a, u: dpg.set_axis_limits("current_y_axis", a, dpg.get_value("curr_y_max")), tag="curr_y_min")
        dpg.add_input_float(label="Max", default_value=10.0, callback=lambda s, a, u: dpg.set_axis_limits("current_y_axis", dpg.get_value("curr_y_min"), a), tag="curr_y_max")

        dpg.add_text("Charge Plot X Axis")
        dpg.add_input_float(label="Min", default_value=0.0, callback=lambda s, a, u: dpg.set_axis_limits("charge_x_axis", a, dpg.get_value("charge_x_max")), tag="charge_x_min")
        dpg.add_input_float(label="Max", default_value=1.0, callback=lambda s, a, u: dpg.set_axis_limits("charge_x_axis", dpg.get_value("charge_x_min"), a), tag="charge_x_max")

        dpg.add_text("Charge Plot Y Axis")
        dpg.add_input_float(label="Min", default_value=0.0, callback=lambda s, a, u: dpg.set_axis_limits("charge_y_axis", a, dpg.get_value("charge_y_max")), tag="charge_y_min")
        dpg.add_input_float(label="Max", default_value=10.0, callback=lambda s, a, u: dpg.set_axis_limits("charge_y_axis", dpg.get_value("charge_y_min"), a), tag="charge_y_max")

    # Imported time offset input
    dpg.add_input_float(label="Imported Data Time Shift (s)", default_value=0.0, callback=lambda s, a, u: update_time_offset(a))

    with dpg.group(horizontal=True):
        dpg.add_button(label="Toggle Shift Charge Plots For Alignment", callback=align_charge_plot_callback)
        dpg.add_button(label="Auto Align Imported Data", callback=auto_align_callback)

dpg.set_primary_window("main_window", True)

def frame_update():
    update_plots()
    dpg.set_frame_callback(dpg.get_frame_count() + 10, frame_update)

dpg.create_viewport(title='MetaShunt Interface', width=1024, height=768)
dpg.setup_dearpygui()
dpg.show_viewport()
frame_update()
dpg.start_dearpygui()
dpg.destroy_context()
