import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import matplotlib.pyplot as plt
import streamlit as st
from io import BytesIO
import base64


clean_df = pd.DataFrame()
dirty_df = pd.DataFrame()


# Functions to generate synthetic data, this should be replaced to real-time sensors data
# we receive from the system thru the ESP32 & some API (Flask?)

def generate_realtime_data(clean=True):
    # introduce random anomaly 3% of the time of generating data
    timestamp = datetime.now()

    #introduce anomalies 3% of the time to simulate possible real-time anomalies / false readings

    if clean and random.random() < 0.03:
        clean = False

    # after the timestamp is created decide if this datapoint will be clean or dirty
    data_point = {
        "timestamp": timestamp,
        "pH": np.random.normal(7.2, 0.1) if clean else np.random.normal(5.5, 0.3),
        "TDS": np.random.normal(50, 10) if clean else np.random.normal(800, 100),
        "turbidity": np.random.normal(0.5, 0.2) if clean else np.random.normal(30, 10),
        #"conductivity": np.random.normal(70, 5) if clean else np.random.normal(900, 50),
        "flow": np.random.normal(1.0, 0.1),
        #"pressure": np.random.normal(1.5, 0.1),
        "temperature": np.random.normal(25, 1)
    }
    return pd.DataFrame([data_point])

def water_clean_data():
    global clean_df
    new_row = generate_realtime_data(clean=True)
    #clean_df.loc[len(clean_df)] = new_row
    clean_df = pd.concat([clean_df, new_row], ignore_index=True)

    # keep only last 24 hr to avoid memory bloating
    timestamp = datetime.now() - timedelta(hours=24)
    clean_df = clean_df[clean_df["timestamp"] >= timestamp]

    return clean_df.reset_index(drop=True)

def water_dirty_data():
    global dirty_df
    new_row = generate_realtime_data(clean=False)

    dirty_df = pd.concat([dirty_df, new_row], ignore_index=True)

    # keep only last 24 hr to avoid memory bloating
    timestamp = datetime.now() - timedelta(hours=24)
    dirty_df = dirty_df[dirty_df["timestamp"] >= timestamp]

    return dirty_df.reset_index(drop=True)


#function to filter data by hour if needed by user
def filter_by_duration(df, hours=1):
    latest_time = df['timestamp'].max()
    start_time = latest_time - pd.Timedelta(hours=hours)
    return df[df['timestamp'] >= start_time]

# deg=fine drinkable water parameters
def healthy_drinkable_water_ranges():
    healthy_data = healthy_ranges = {
    "pH": (6.5, 8.5),
    "TDS": (0, 1000),
    "turbidity": (0, 1),
    #"conductivity": (0, 500),
    "flow": (0.5, 5),
    #"pressure": (1, 3),
    "temperature": (24, 26)}

    return healthy_data


# Trying to simulate injection of anomalies into the dataset to simulate the alerting system

def inject_anomalies(df, num_anomalies=20):
    for _ in range(num_anomalies):
        # inject within the last 5 minutes
        timestamp = datetime.now() - timedelta(minutes=np.random.uniform(0, 5))

        anomaly_data = {
            "timestamp": timestamp,
            "pH": np.random.normal(8.5, 0.1),
            "TDS": np.random.normal(900, 50),
            "turbidity": np.random.normal(35, 5),
            #"conductivity": np.random.normal(950, 20),
            "flow": np.random.normal(6, 0.05),
            #"pressure": np.random.normal(3.5, 0.1),
            "temperature": np.random.normal(29, 1)
        }

        df = pd.concat([df, pd.DataFrame([anomaly_data])], ignore_index=True)
    return df


def calculate_wqi(pH, tds, turbidity):
    # Normalize parameters to 0–100 scale

    pH_index = 100 if 6.5 <= pH <= 8.5 else max(0, 100 - min(abs(pH - 7), abs(pH - 7.5)) * 30)
    pH_index = min(pH_index, 100)

    tds_index = 100 if tds < 300 else max(0, 100 - tds * 0.1)
    tds_index = min(tds_index, 100)

    turbidity_index = 100 if turbidity < 1 else max(0, 100 - (turbidity - 5) * 10)
    turbidity_index = min(turbidity_index, 100)

    wqi = (pH_index + tds_index + turbidity_index) / 3

    return round(min(wqi, 100), 2)

# Function to create parameter plots-trends for selected user duration to view as a background for the avg cards in the summary page
def create_trend_background(df, column):
    fig, ax = plt.subplots(figsize=(3, 1.5))
    ax.plot(df["timestamp"], df[column], color='#2196F3', linewidth=2)
    ax.axis('off')
    fig.patch.set_alpha(0)  # transparent figure background
    ax.patch.set_alpha(0)   # transparent axis background

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', transparent=True)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{encoded}"
