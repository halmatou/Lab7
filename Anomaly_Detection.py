from data_utils import healthy_drinkable_water_ranges
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
import streamlit as st

#Anamolies/alerts
#define a function to detect differences compared to drinkable water (Simple statistical method)
def detect_anomalies(df, time_window=5): # time in minutes
    # check the last value
    #last_value = df.iloc[-1]

    # to make sure the anomalies are actual warning alerts
    # we need to ensure its not just a single false reading and that the problem is persistent
    # we will look at the average of the data for last 5 min and compare it to our mai

    # Define the detection time window
    threshold = datetime.now() - timedelta(minutes=time_window)
    # read the data for this time window
    time_window_data = df[df['timestamp'] >= threshold]

    alert = []

    for parameter, (min_, max_) in healthy_drinkable_water_ranges().items():

        # read data for time window for each parameter
        recent_values = time_window_data[parameter]

        # find the average of this data
        average_val = recent_values.mean()

        if average_val < min_ or average_val > max_:

            alert.append({
                'parameter': parameter,
                'value': round(average_val, 2),
                'status': 'High' if average_val > max_ else 'Low',
                'range': f"{min_} - {max_}",
                'time_window': f"Last {time_window} minutes (Average)"
            })

        #if parameter in last_value and (last_value[parameter] < min_ or last_value[parameter] > max_):
         #   alert.append({'parameter': parameter, 'value': round(last_value[parameter],2),
          #                'Alert': 'High' if last_value[parameter] > max_ else 'Low'})
    return alert

# AI Method
#Sensor malfunctions or spikes (e.g., extreme pH, TDS).
#Filter performance issues (e.g., gradual increase in turbidity or TDS).
#Pressure or flow abnormalities that might indicate clogs or leaks.

last_trained = None
isolation_model = None

def train_isolation_forest(df):
    '''This function is to detect anomalies using AI model isolation forest
         the idea is to train the model on historical clean data to help it detect changes
         to keep the model up to date, it will retrain every 24 hours
         this way anomalies for each parameter will be easily cross checked with "normal" clean data of the system '''


    global isolation_model, last_trained
    #st.write("Training Isolation Forest model...")

    features = ['pH', 'TDS', 'turbidity', 'flow', 'temperature']

    X = df[features]

    model = IsolationForest(contamination=0.03, random_state=42)

    model.fit(X)

    st.session_state['isolation_model'] = model
    st.session_state['last_trained'] = datetime.now()

def isolation_forest_detection(df):
    global isolation_model, last_trained

    if 'isolation_model' not in st.session_state or 'last_trained' not in st.session_state or \
            datetime.now() - st.session_state['last_trained'] > timedelta(hours=24):
        train_isolation_forest(df)

    model = st.session_state['isolation_model']
    features = ['pH', 'TDS', 'turbidity', 'flow', 'temperature']
    df['anomaly'] = model.predict(df[features])
    return df


def isolation_forest_detection_(df):

    # initialize isolation forest model , parameters can be tuned (gridsearch)
    iso_forest = IsolationForest(contamination=0.05, random_state=42)

    features = ['pH', 'TDS', 'turbidity', 'flow', 'temperature']

    if len(df) < 10:
        return df.assign(anomaly=0)  # Not enough data to train

    model_input = df[features]
    df['anomaly'] = iso_forest.fit_predict(model_input)

    return df




