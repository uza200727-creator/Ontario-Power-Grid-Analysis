import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import os


# Url for the current grid data from IESO, it updates every hour with the latest data
URL = "https://reports-public.ieso.ca/public/GenOutputCapability/PUB_GenOutputCapability.xml"

# Function to get text that makes sure program doesn't crash if a tag is missing
def get_safe_text(element, tag_name):
    if element is None:
        return None
    child = element.find(tag_name)
    if child is None:
        return None
    return child.text



def fetch_grid_data():
    print(f"Starting connection:", end=" ")
    # Act as a browser agent so we can get access to the URL and data in it from IESO
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(URL, headers=headers)
        #Prints error and stops program if there are any errors
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return None

        print("No errors")
        
        #Takes in XML data from file and turns into a tree structure we can look up, then removes any namespaces in the data that could interfere with us trying to find data names
        xml_content = response.content.decode('utf-8')
        root = ET.fromstring(xml_content)
        for elem in root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]

      

    
        valid_hour = 0
        
        # Check all generators to find the latest valid hour
        for gen in root.findall(".//Generator"):
            outputs = gen.find("Outputs")
            if outputs is None: continue
            
            for out in outputs.findall("Output"):
                # Try to get energy used, but don't crash if missing
                val_text = get_safe_text(out, "EnergyMW")
                hour_text = get_safe_text(out, "Hour")
                
                if val_text and hour_text:
                    if float(val_text) > 0:
                        valid_hour = max(valid_hour, int(hour_text))
     #If valid hour has not changed, that means that the output for the current hour is 0 (not filled in yet) so we need to go back and use hour 1 as default.
        if valid_hour == 0:
          
            valid_hour = 1
        else:
            print(f"Using Hour {valid_hour}")

        # Creating list to store data
        data = []
        for gen in root.findall(".//Generator"):
            # For each generator, get the name and type of fuel
            name = get_safe_text(gen, "GeneratorName")
            fuel_type = get_safe_text(gen, "FuelType")
            
            output_val = 0.0
            # Find outputs for the generators for the valid hour we found (2 AM or the first hour)
            outputs = gen.find("Outputs")
            if outputs is not None:
                for out in outputs.findall("Output"):
                    h_text = get_safe_text(out, "Hour")
                    if h_text and int(h_text) == valid_hour:
                        val_text = get_safe_text(out, "EnergyMW")
                        if val_text:
                            output_val = float(val_text)
                        break
            # If we have a name and fuel type existing, add the generator's data to our list 
            if name and fuel_type:
                data.append({
                    "Timestamp": f"Hour {valid_hour}",
                    "Generator": name,
                    "Fuel": fuel_type,
                    "Output_MW": output_val
                })
        
        # Convert the list of data into a DataFrame table and return it
        return pd.DataFrame(data)

# If there are any errors in the above code, print the error 
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None
#If run in main, run the function
if __name__ == "__main__":
    df = fetch_grid_data()
    
    # Display our data and save it to a CSV file
    if df is not None and not df.empty:
        print(f"\n Current grid data:")
        mix = df.groupby("Fuel")["Output_MW"].sum().sort_values(ascending=False)
        print(mix)
        
        os.makedirs("data/raw", exist_ok=True)
        filename = f"data/raw/grid_status.csv"
        df.to_csv(filename, index=False)
        print(f"\n Saved data")