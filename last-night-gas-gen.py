import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Where data is sourced from
BASE_DIR = "https://reports-public.ieso.ca/public/GenOutputCapability"
#Timezone for Ontario set
USER_TZ = ZoneInfo("America/Toronto")
#If no text exists, return none instead of crashing
def get_safe_text(element, tag_name):
    if element is None:
        return None
    child = element.find(tag_name)
    return child.text if child is not None else None

#Remove tags that exist in the XML data so data finding works
def strip_namespaces(root):
    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]
    return root

#Find gas total at a specific hour and specific date, in this case we are looking at 2 AM
def fetch_gas_total_at_hour_for_date(target_date, target_hour=2, timeout=20):
  # Create a url that points to an XML file for the target date (last night)
    date_str = target_date.strftime("%Y%m%d")
    url = f"{BASE_DIR}/PUB_GenOutputCapability_{date_str}.xml"

# Act like a browser agent to have access to the website and IESO date, then request the XML data with the url to the IESO website
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=timeout)
    
# Convert the XML file into text, and strip out namespaces and extra tags like URLs at the start
    try:
        root = ET.fromstring(r.content.decode("utf-8"))
        root = strip_namespaces(root)
# If the error is not found return instead of crashing
    except Exception as e:
        return None, url, f"XML parse error: {e}"

    total_gas = 0.0
#Find all fuel types, and strip of upper case
    for gen in root.findall(".//Generator"):
        fuel_type = get_safe_text(gen, "FuelType")
        if fuel_type:
            fuel_type = fuel_type.strip().upper()

        # Only search for gas generators
        if fuel_type != "GAS":
            continue


#Find outputs for gas generators, make sure output exists
        outputs = gen.find("Outputs")
        if outputs is None:
            continue

#Get hour for outsputs 
        for out in outputs.findall("Output"):
            h_text = get_safe_text(out, "Hour")
            if not h_text:
                continue

            #Make sure the hour we found matches the target of 2 AM
            try:
                if int(h_text) != int(target_hour):
                    continue
            except ValueError:
                continue
#Get energy outputs for gas, add it to total
            val_text = get_safe_text(out, "EnergyMW")
            try:
                total_gas += float(val_text) if val_text else 0.0
            except ValueError:
                # Ignores value errors that come usually from bad formatting
                pass

            break  

        #Return values we need

    return total_gas, url, None
#Takes average gas at a specific hour for the last n nights, in our case we are targetting 2 AM
def average_gas_at_hour_last_n_nights(n_nights=7, target_hour=2):
  
    # Creates a date for last night based on what today is 
    today_local = datetime.now(USER_TZ).date()
    last_night_date = today_local - timedelta(days=1)

    rows = []
    totals = []
# Loops through last n lights, getting gas total at 2 AM for each night and then adding it to a list. If no output taken adds an "error" row so we can tell something went wrong
    for i in range(n_nights):
        d = last_night_date - timedelta(days=i)
        total, url, err = fetch_gas_total_at_hour_for_date(d, target_hour=target_hour)

        if total is None:
            rows.append({"Date": d.isoformat(), "Gas_2AM_MW": None, "Status": err, "Source": url})
        else:
            rows.append({"Date": d.isoformat(), "Gas_2AM_MW": total, "Status": "OK", "Source": url})
            totals.append(total)
# Creates a table with the gas totals sorted by date
    df = pd.DataFrame(rows).sort_values("Date")
#Sorting the table's data to make sure that the last row is last night, and then getting the gas total from last night
    last_night_total = None
    if not df.empty:
        # last row is last_night_date after sorting ascending
        last_row = df[df["Date"] == last_night_date.isoformat()]
        if not last_row.empty:
            last_night_total = last_row["Gas_2AM_MW"].iloc[0]
#Calculaing the average gas total at 2 AM for the past 7 nights
    avg_total = (sum(totals) / len(totals)) if totals else None
    return last_night_date, last_night_total, avg_total, df
#If running in main.py, define our target hour and n last nights then run the program
if __name__ == "__main__":
    TARGET_HOUR = 2
    N_NIGHTS = 7  

    last_date, last_total, avg_total, details = average_gas_at_hour_last_n_nights(
        n_nights=N_NIGHTS,
        target_hour=TARGET_HOUR
    )


#Displaying our data 
    print("\n" + "=" * 55)
   

    if last_total is not None:
        print(f"{last_total:,.2f} MW")
  


        print(f"7-night average: {avg_total:>15,.2f} MW")
        
   

