import ctypes
import os
import pandas as pd

# Create a .dll version of our battery simulation that lets us call C functions from Python
lib_path = os.path.abspath("simulation/battery_sim.dll")
battery_lib = ctypes.CDLL(lib_path)

# Create a battery object structure with the required parameters
class Battery(ctypes.Structure):
    _fields_ = [
        ("capacity_mwh", ctypes.c_float),
        ("current_charge", ctypes.c_float),
        ("efficiency", ctypes.c_float),
        ("max_power_mw", ctypes.c_float)
    ]

# Create a battery object with 10MWh capacity, no initial charge, 90% efficiency, and 2MW max power
my_battery = Battery(10.0, 0.0, 0.9, 2.0)


def run_simulation():
    # Define a hypothetical excess power we want to charge with
    excess_power = 5.0 
    
    
    print(f"Sending {excess_power}MW...")
    
    # Call the C function charge_battery with our excess power 
    battery_lib.charge_battery(ctypes.byref(my_battery), ctypes.c_float(excess_power))
#Run file if in main.py
if __name__ == "__main__":
    run_simulation()