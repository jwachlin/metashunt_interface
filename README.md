# MetaShunt

MetaShunt is a **precision current measurement tool** designed for analyzing ultra-low power and IoT devices. It measures current across a wide dynamic range — from **nanoamps to amps** — making it ideal for tasks like verifying battery life, characterizing low-power modes, and debugging energy usage.

---

## Features

* Wide measurement range: **nA → A**
* High accuracy and high resolution
* USB-powered and compact form factor
* Real-time data visualization with GUI support
* Python logging and scripting tools for use in automated testing

<img width="653" height="435" alt="image" src="https://github.com/user-attachments/assets/b802d9b3-1cc1-40c4-8b2c-198d6b765890" />

---

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/jwachlin/metashunt_interface.git
   cd ./metashunt_interface
   ```
2. Install Python dependencies as needed.

3. Connect MetaShunt to your computer via USB.

---

## Quick Start

### Hardware Setup

1. Connect the terminals of MetaShunt with your device under test (DUT) as shown in the user guide.
2. Connect MetaShunt to your computer over USB.

### Software Setup

Run the GUI (MetaShunt V2 only):

```bash
cd ./GUI
python metashunt_v2_gui.py
```

Or collect data and generate plots with script example:

(For MetaShunt V1, 10 second measurement)
```bash
cd ./Realtime\ Interface
python metashunt_realtime_interface.py s 10
```

(For MetaShunt V2, 10 second measurement)
```bash
cd ./Realtime\ Interface
python metashunt_realtime_v2_interface.py s 10
```

---

## Usage

### Graphical Interface

* Displays **real-time current plots**
* Zoom and pan to analyze low-power events
* Export data to CSV for further processing
* Compare past measurements to see how your changes impact current

### CLI / Logging

* Stream current readings directly over USB
* Save logs for long-term analysis
* Integrate with scripting environments for automated testing

---

## Example Applications

* **Battery life estimation**: Measure sleep vs active currents
* **Low-power optimization**: Verify microcontroller STOP/IDLE modes
* **Power profiling**: Analyze wireless transmission spikes
* **Regression testing**: Compare firmware versions for energy consumption differences

---

## Documentation

* [Version 1 User Guide](https://github.com/jwachlin/metashunt_interface/blob/main/MetaShunt%20User%20Guide%20V1.0.pdf)
* [Version 2 User Guide](https://github.com/jwachlin/metashunt_interface/blob/main/MetaShunt%20V2%20User%20Guide.pdf)

---

## Contributing

Please submit issues for bugs or feature requests.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
