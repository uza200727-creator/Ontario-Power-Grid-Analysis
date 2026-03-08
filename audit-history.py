import pandas as pd
import requests
import io

#URL for the file that we are extracting data from
URL_202102 = "https://reports-public.ieso.ca/public/GenOutputCapabilityMonth/PUB_GenOutputCapabilityMonth_202102.csv"


#
def load_ieso_month_csv(text: str) -> pd.DataFrame:
   # Splits file into lines, and then looks to find the header row so we dont have any empty rows being used for data
    lines = text.splitlines()
    header_idx = None
    for i, line in enumerate(lines[:100]):
        if line.strip().startswith("Delivery Date,"):
            header_idx = i
            break



    csv_text = "\n".join(lines[header_idx:])

    # Deletes any unnamed columns and takes off empty space
    df = pd.read_csv(io.StringIO(csv_text), index_col=False)
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.match(r"^Unnamed")]  

    return df

def run_2021_audit():
    #Act like a browser agent so we are given access to the website and data
    headers = {"User-Agent": "Mozilla/5.0"}
    print(f"Requesting data")


#Request data, if error print error
    try:
        r = requests.get(URL_202102, headers=headers, timeout=20)
        if r.status_code != 200:
            print(f"Data request failed with status code {r.status_code}")
            return None

        df = load_ieso_month_csv(r.text)

        required = ["Delivery Date", "Generator", "Fuel Type", "Measurement", "Hour 2"]
     

        # Converts all these string values into strings, upper case with no empty spaces
        df["Fuel Type"] = df["Fuel Type"].astype(str).str.strip().str.upper()
        df["Measurement"] = df["Measurement"].astype(str).str.strip().str.upper()
        df["Delivery Date"] = pd.to_datetime(df["Delivery Date"], errors="coerce")
        df["DateOnly"] = df["Delivery Date"].dt.date

        # Filter data table for gas and output
        df_gas_output = df[(df["Fuel Type"] == "GAS") & (df["Measurement"] == "OUTPUT")].copy()
        if df_gas_output.empty:
            print("⚠️ No GAS+OUTPUT rows found after filtering.")
            print("Fuel Type top values:", df["Fuel Type"].value_counts().head(10))
            print("Measurement top values:", df["Measurement"].value_counts().head(10))
            return None

        # Convert the hour we want, 2 AM, to numbers and remove empty spaces and commas
        df_gas_output["Hour 2"] = (
            df_gas_output["Hour 2"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df_gas_output["Hour 2"] = pd.to_numeric(df_gas_output["Hour 2"], errors="coerce")

        # Get the average gas output at 2 AM for every day of Feb 2021, then get the average of the daily totals
        daily_totals = df_gas_output.groupby("DateOnly")["Hour 2"].sum()
        avg_total_hour2 = daily_totals.mean()

        print("\n" + "—" * 60)
        print("February 2021 Gas Output Average at 2 AM")
        print(f"{avg_total_hour2:,.2f} MW")
        print("—" * 60)

        return float(avg_total_hour2)

    except Exception as e:
        print(f"Error: {e}")
        return None
#Run if main
if __name__ == "__main__":
    run_2021_audit()