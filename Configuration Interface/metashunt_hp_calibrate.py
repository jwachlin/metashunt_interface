import numpy as np
import json
import sys 

V_bus = 4.947

lower_current_resistor_ohm = 22.05
lower_current_measured_amp = 0.227

higher_current_resistor_ohm = 11.10
higher_current_measured_amp = 0.4741

if(len(sys.argv) > 1):
    config_file_name = sys.argv[1]

    f = open(config_file_name)

    config_data = json.load(f)

    gain = (1.0 + config_data["R13"]/config_data["R15"]) * (1.0 + config_data["R14"]/config_data["R16"])
    amplification_gain_inv = (1.0 / gain) * ((1000.0 * 3.0) / 4095.0)

    print("Current gain is {0}".format(gain)) 

    lp_fet_r_current = config_data["R_LP_FET"]
    hp_fet_r_current = config_data["R_HP_FET"]

    r_eff_current = np.zeros((8,1))
    r_eff_current[0] = config_data["R7"]
    r_eff_current[1] = 1.0/((1.0/(config_data["R6"]+lp_fet_r_current)) + (1.0/r_eff_current[0]))
    r_eff_current[2] = 1.0/((1.0/(config_data["R8"]+lp_fet_r_current)) + (1.0/r_eff_current[1]))
    r_eff_current[3] = 1.0/((1.0/(config_data["R9"]+lp_fet_r_current)) + (1.0/r_eff_current[2]))
    r_eff_current[4] = 1.0/((1.0/(config_data["R10"]+lp_fet_r_current)) + (1.0/r_eff_current[3]))
    r_eff_current[5] = 1.0/((1.0/(config_data["R12"]+lp_fet_r_current)) + (1.0/r_eff_current[4]))
    r_eff_current[6] = 1.0/((1.0/(config_data["R23"]+hp_fet_r_current)) + (1.0/r_eff_current[5]))
    r_eff_current[7] = 1.0/((1.0/(config_data["R25"]+hp_fet_r_current)) + (1.0/r_eff_current[6]))

    # Calculate what actual current is
    lower_current_actual_amp = V_bus / lower_current_resistor_ohm
    higher_current_actual_amp = V_bus / higher_current_resistor_ohm

    # Calculate what correct effective resistance is
    r_eff_lower_current = (lower_current_measured_amp * r_eff_current[6]) / lower_current_actual_amp
    r_eff_higher_current = (higher_current_measured_amp * r_eff_current[7]) / higher_current_actual_amp

    print("Lower level effective resistance was set to: {0} Ohm, but is actually {1} Ohm".format(r_eff_current[6], r_eff_lower_current))
    print("Higher level effective resistance was set to: {0} Ohm, but is actually {1} Ohm".format(r_eff_current[7], r_eff_higher_current))

    # Calculate hp_fet_r_current to calibrate 7th level
    hp_fet_r_new = (r_eff_lower_current/(1.0 - r_eff_lower_current /r_eff_current[5] )) - config_data["R23"]
    print("Updated R_HP_FET is {0} Ohm, but was {1} Ohm".format(hp_fet_r_new, hp_fet_r_current))

    # Adjust R25 to calibrate 8th level
    # Note: We only care about total, it is just lumped, so OK approach
    r25_new = (r_eff_higher_current/(1.0 - r_eff_higher_current/r_eff_lower_current)) - hp_fet_r_new
    print("Updated R25 is {0} Ohm, but was {1} Ohm".format(r25_new, config_data["R25"]))

else:
    print("Please provide the current configuration JSON file")