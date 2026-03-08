import ctypes
import os
from scraper.fetch_ieso import fetch_grid_data
# Carbon emission  in grams CO2 per kWh for each fuel type
CARBON_MAP = {
    "NUCLEAR": 12,        # Median from image
    "HYDRO": 24,          # Median from image (Global average)
    "WIND": 11,           # Median for Onshore Wind
    "SOLAR": 48,          # Median for Utility Scale PV
    "GAS": 490,           # Median for Combined Cycle Gas
    "BIOFUEL": 230,       # Median for Dedicated Biomass
    "OTHER": 38           # Using Geothermal as a proxy for "Other"
}


# Create .dll structure that allows us to call battery functions and data
lib_path = os.path.abspath("simulation/battery_sim.dll")
battery_lib = ctypes.CDLL(lib_path)

# Create a class for the battery object that matches the C parameters
class Battery(ctypes.Structure):
    _fields_ = [("capacity_mwh", ctypes.c_float),
                ("current_charge", ctypes.c_float),
                ("efficiency", ctypes.c_float),
                ("max_power_mw", ctypes.c_float)]

# Create a battery object with 10MWh capacity, no initial charge, 90% efficiency, and 2MW max power
my_battery = Battery(10.0, 0.0, 0.9, 2.0)

def run_system():
    # Call function that gets grid data and returns a table with grid and fuel usage data
    df = fetch_grid_data()
    if df is None: return

    # Get total power output
    total_mw = df['Output_MW'].sum()
    # Get total gas power output
    gas_mw = df[df['Fuel'] == 'GAS']['Output_MW'].sum()
    #Calculate percent of total power that is gas
    gas_percent = (gas_mw / total_mw) * 100

    print(f"\nGas Percentage: {gas_percent:.1f}%")

    #If gas percentage is lower than average (16.6%), the grid is considered clean and the virtual battery is charged. Otherwise, it is considered dirty and the battery is not charged
    if gas_percent < 16.6:
        print("Grid is clean, charge battery")
        # The C function to charge the battery is called with a speed of 2MW
        battery_lib.charge_battery(ctypes.byref(my_battery), ctypes.c_float(2.0))
    else:
        print("Grid is dirty, battery holding charge")
# If the file name is main, run the main function
if __name__ == "__main__":
    run_system()