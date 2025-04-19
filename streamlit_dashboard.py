import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from streamlit_extras.metric_cards import style_metric_cards
from data_utils import water_clean_data, water_dirty_data, inject_anomalies, healthy_drinkable_water_ranges, calculate_wqi, create_trend_background
from Styling import metric_color, metric_style, metric_style_
from Anomaly_Detection import detect_anomalies, isolation_forest_detection
import time

# set up page
st.set_page_config(page_title="Smart Water Purification Dashboard", layout="wide")
# Title
st.title("💧 Smart Water Quality Monitoring")



# Create a sidebar for user to choose between different view options
st.sidebar.title("🔍 View")
# List the view options we need (can add more anytime)
view_options = st.sidebar.radio("Select Data to View:", ['Home', 'Clean Water', 'Dirty Water', 'System Maintenance'])

# If statement to help add information to each view option
if view_options == 'Home':
    st.subheader("📊 Overall System Insights")
    st.info('This section summarizes important insights')

    st.subheader("")
    #create time filter
    time_filter = st.selectbox("Select time range in hours", [1,6,12,24], index=0, format_func=lambda x: f"{x} hour(s)")

    st_autorefresh(interval=5000, key="clean_data_refresh")

    clean_df = water_clean_data()

    ##############################################

    clean_df_ = isolation_forest_detection(clean_df)

    # Filter detected anomalies
    ai_alerts = clean_df_[clean_df_['anomaly'] == -1] #.tail(5)  # Last 5 anomalies if any

    if "ai_alerts" not in st.session_state:
        # store ai alerts so we can show them longer
        st.session_state.ai_alerts = []
    expected_ranges = healthy_drinkable_water_ranges()
    with st.sidebar:
        if not ai_alerts.empty:
            st.subheader("🚨 AI-Detected Anomalies")
            for _, row in ai_alerts.iterrows():
                issues = []
                #for col in ["pH", "TDS", "turbidity", "conductivity", "flow", "pressure", "temperature"]:
                #    issues.append(f"{col}: <code>{round(ai_alerts[col], 2)}</code>")

                for param, (min_val, max_val) in expected_ranges.items():
                    if param in row and (row[param] < min_val or row[param] > max_val):
                        issues.append(f"{param}: {round(row[param], 2)} (Expected: {min_val}-{max_val})")
                if issues:
                    st.markdown(f"""
                        <div style="border: 2px solid red; padding: 6px 10px; border-radius: 5px;
                                    background-color: rgba(255, 80, 80, 0.3); margin: 5px 0;">
                            <strong>Anomaly detected</strong> at <code>{row['timestamp'].strftime('%H:%M:%S')}</code><br/>
                            pH: {round(row['pH'], 2)}, TDS: {round(row['TDS'], 2)}, Turbidity: {round(row['turbidity'], 2)}...
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ No anomalies detected by AI.")

        #####################


    if "anomalies_injected" not in st.session_state:
        clean_df = inject_anomalies(clean_df)
        st.session_state.anomalies_injected = True


    last_timestamp = clean_df["timestamp"].iloc[-1]
    start_time = last_timestamp - pd.Timedelta(hours=time_filter)
    filtered_data = clean_df[clean_df["timestamp"] >= start_time]

    if filtered_data.empty:
        st.warning("No data for the selected duration, please select a different time")
    else:
        # find average values for the selected duration
        averages = {'pH': round(filtered_data['pH'].mean(),2),
                    'TDS (mg/L)': round(filtered_data['TDS'].mean(),2),
                    'Turbidity (NTU)': round(filtered_data['turbidity'].mean(),2),
                    'Flow Rate (L/min)': round(filtered_data['flow'].mean(),2),
                    'Temperature (°C)': round(filtered_data['temperature'].mean(),2)}

        avg_ph = averages.get("pH", None)
        bg_ph = create_trend_background(filtered_data, "pH")
        ph_data = filtered_data['pH'].tolist()
        tds_data = filtered_data['TDS'].tolist()
        turb_data = filtered_data['turbidity'].tolist()
        flow_data = filtered_data['flow'].tolist()
        temp_data = filtered_data['temperature'].tolist()

        avg_tds = averages.get("TDS (mg/L)", None)
        bg_tds = create_trend_background(filtered_data, "TDS")

        avg_turbidity = averages.get("Turbidity (NTU)", None)
        bg_tur = create_trend_background(filtered_data, "turbidity")

        bg_flow = create_trend_background(filtered_data, "flow")
        bg_temp = create_trend_background(filtered_data, "temperature")

        #if avg_ph is not None and avg_tds is not None and avg_turbidity is not None:
        wqi_score = calculate_wqi(avg_ph, avg_tds, avg_turbidity)

        # color code the % to show if quality is good or bad
        if wqi_score >= 90:
            bar_color = "#4CAF50"  # Green / excellent
            wqi_comment = "💧 Excellent Performance"

        elif wqi_score >= 80:
            bar_color = "#FFEB3B"  # Yellow / check system for cleaning
            wqi_comment = "🧹 System cleanup recommended"

        else:
            bar_color = "#F44336"  # Red / hazard perform maintenance
            wqi_comment = "⚠️ Poor performance, perform system maintenance"

        wqi_percent = max(0, min(wqi_score, 100))


        st.markdown(f"""
            <style>
            .wqi-wrapper {{
                display: flex;
                align-items: center;
                gap: 20px;
            }}

            .wqi-container {{
                width: 60%;
                min-width: 200px;
                position: relative;
            }}

            .wqi-bar {{
                position: relative;
                width: 100%;
                height: 35px;
                background: linear-gradient(to right, 
                    #F44336 0%, #F44336 80%, 
                    #FFEB3B 80%, #FFEB3B 90%, 
                    #4CAF50 90%, #4CAF50 100%);
                border-radius: 10px;
                margin-bottom: 10px;
            }}

            .wqi-pointer {{
                position: absolute;
                left: {wqi_percent}%;
                bottom: -10px;
                transform: translateX(-50%) rotate(180deg);
                font-size: 25px;
                color: white;
                font-weight: bold;
            }}

            .wqi-ticks {{
                position: relative;
                top: 45px;
                left: 0;
                width: 100%;
                height: 20px;
            }}
            .wqi-ticks span {{
                position: absolute;
                transform: translateX(-50%);
                font-size: 12px;
                color: white;
            }}
            
            .wqi-comment {{
                font-size: 16px;
                font-weight: 600;
                color: white;
                padding: 2px 4px;
                background-color: rgba(255, 193, 7, 0.15);
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                max-width: 300px;
            }}
            </style>

            <div class="wqi-wrapper">
                <div class="wqi-container">
                    <div style="margin-bottom: 5px; font-weight: bold;">Water Quality Index (WQI): {wqi_score:.2f}%</div>
                    <div class="wqi-bar">
                        <div class="wqi-pointer">▲</div>
                        <div class="wqi-ticks">
                        <span style="left: 0%;">0</span>
                        <span style="left: 20%;">20</span>
                        <span style="left: 40%;">40</span>
                        <span style="left: 60%;">60</span>
                        <span style="left: 80%;">80</span>
                        <span style="left: 90%;">90</span>
                        <span style="left: 100%;">100</span>
                    </div>
                    </div>
                </div>
                <div class="wqi-comment">{wqi_comment}</div>
            </div>
        """, unsafe_allow_html=True)



        #else:
         #   st.warning("Not enough data to calculate WQI.")

        st.subheader("")
        st.subheader("Water Quality Overview")
        with st.container():
            col1, col2, col3 = st.columns(3)

            with col1:
                metric_style("Average pH", averages['pH'],"",metric_color(averages["pH"],"pH"))
                metric_style("Average Temperature", averages['Temperature (°C)'], "(°C)", metric_color(averages["Temperature (°C)"],"temperature"))

            with col2:
                metric_style("Average TDS", averages['TDS (mg/L)'],"(mg/L)", metric_color(averages["TDS (mg/L)"],"TDS"))
                #metric_style("Average conductivity", averages['Conductivity (µS/cm)'],"(µS/cm)", metric_color(averages["Conductivity (µS/cm)"],"conductivity"))
                metric_style("Average Turbidity", averages['Turbidity (NTU)'],"(NTU)", metric_color(averages["Turbidity (NTU)"],"turbidity"))

            with col3:
                #metric_style("Average Pressure", averages['Pressure (bar)'],"(bar)", metric_color(averages["Pressure (bar)"],"pressure"))
                metric_style("Average Flow", averages['Flow Rate (L/min)'],"(L/min)", metric_color(averages["Flow Rate (L/min)"],"flow"))




    st.subheader(' ')


    st.markdown("🚨 Alerts & Anomalies")

    alerts = detect_anomalies(clean_df)

    if alerts:
        for alert in alerts:
            st.markdown(f""" 
                        <div style= " border: 2px solid red;
                        padding: 6px 10px;
                        border-radius: 5px;
                        background-color: rgba(255, 80, 80, 0.4);
                        font-size: 0.9rem;
                        margin: 5px 0;">
                        <strong>{alert['parameter']}</strong>
                        at <strong>{alert['value']}</strong><br/>
                        Expected range: <code>{alert['range']}</code>
                        </div>""", unsafe_allow_html=True)

    else:
        st.success("All Parameters are within drinkable limits")

elif view_options == 'Clean Water':

    st.subheader("🔵 Clean Water Monitoring")
    st.info("This section shows clean water quality monitoring data")

    # Auto-refresh every 5 seconds
    st_autorefresh(interval=5000, key="clean_data_refresh")

    #Create a time filter for user to filter data
    #hours = st.slider("Select duration (hours)", 1, 24, 1)

    # call the generated data (in actual system call sensors data)
    df_clean = water_clean_data()

    #Plotting data
    # plot into 3 columns
    col1, spacer1, col2, spacer2, col3 = st.columns([1, 0.1, 1, 0.1, 1])

    #plotting pH level as a gauge
    with col1:
        ph_level = round(df_clean['pH'].iloc[-1],2)
        gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value=ph_level,
            domain={"x": [0, 1], "y": [0,1]},
            title = {'text':"Ph Level"},
            gauge= {'axis': {'range': [0,14], 'tickmode': 'linear','tick0': 0,'dtick':2, 'tickfont': {'size': 14} },
                    'bar': {'color': 'blue'},
                    'steps': [{'range': [0, 6.5], 'color': "red"},
                    {'range': [6.5, 9.5], 'color': "green"},
                    {'range': [9.5, 14], 'color': "orange"},
                    ]}
        ))

        gauge.update_layout(height=400,margin=dict(t=5, b=5, l=20, r=25))
        st.plotly_chart(gauge, use_container_width=True)

    with col2:
        # Plot temperature as a gauge meter
        temp_value = df_clean["temperature"].iloc[-1]
        thermostat_fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = temp_value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title = {'text':"Temperature (°C)"},
            gauge = {'axis': {'range': [0,60], 'tickmode': 'linear','tick0': 0,'dtick':10,'tickwidth': 1, 'tickcolor': 'darkgray'},
                        'bar': {'color': 'blue'},
                        'steps': [{'range': [0, 30], 'color': "#81D4FA"},
                              {'range': [30, 60], 'color': "#FFB74D"}],
                    'threshold': {'line': {'color': "black", 'width': 4},
                                  'thickness': 0.75,'value': temp_value}},
        ))

        thermostat_fig.update_layout(height = 400,margin=dict(t=5, b=5, l=20, r=20))
        st.plotly_chart(thermostat_fig, use_container_width=True)

    with col3:
        # show last flow rate and pressure data as single values
        last_row = df_clean.iloc[-1]
        st.markdown("### ") # to add vertical space for better visual only
        #st.metric(label="Pressure (bar)", value=f"{last_row['pressure']:.2f}")
        st.metric(label="Flow Rate (L/min)", value=f"{last_row['flow']:.2f}")
        style_metric_cards(background_color="#000000", border_left_color="#d6d6d6")

    # Plot other charts

    st.subheader("TDS")
    tds_fig = px.area(df_clean, x="timestamp", y="TDS", title="TDS (mg/L)")
    tds_fig.update_traces(line_color='deeppink')
    st.plotly_chart(tds_fig, use_container_width=True)

    #st.subheader("Conductivity")
    #st.plotly_chart(px.line(df_clean, x="timestamp", y="conductivity", title="Conductivity (µS/cm)"),
     #                   use_container_width=True)

    st.subheader("Turbidity")
    tur_fig = px.line(df_clean, x="timestamp", y="turbidity", title="Turbidity (NTU)")
    tur_fig.update_traces(line= dict(color='mediumorchid'))
    st.plotly_chart(tur_fig,use_container_width=True)




elif view_options == 'Dirty Water':
    st.subheader("🟠 Dirty Water Monitoring")
    st.info("This section shows dirty water quality monitoring data")

    # Create a time filter for user to filter data
    #hours = st.selectbox("Select Duration:", [1, 6, 12, 24], index=0)
    df_dirty = water_dirty_data()
    #filtered_dirty_df = filter_by_duration(df_dirty, hours)

    # Auto-refresh every 5 seconds
    st_autorefresh(interval=5000, key="dirty_data_refresh")


    # Plotting data
    # plot into 3 columns
    col1, spacer1, col2, spacer2, col3 = st.columns([1, 0.1, 1, 0.1, 1])

    # plotting pH level as a gauge
    with col1:
        ph_level = round(df_dirty['pH'].iloc[-1], 2)
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=ph_level,
            domain={"x": [0, 1], "y": [0, 1]},
            title={'text': "Ph Level"},
            gauge={'axis': {'range': [0, 14], 'tickmode': 'linear', 'tick0': 0, 'dtick': 2, 'tickfont': {'size': 14}},
                   'bar': {'color': 'blue'},
                   'steps': [{'range': [0, 6.5], 'color': "red"},
                             {'range': [6.5, 9.5], 'color': "green"},
                             {'range': [9.5, 14], 'color': "orange"},
                             ]}
        ))

        gauge.update_layout(height=400, margin=dict(t=5, b=5, l=20, r=25))
        st.plotly_chart(gauge, use_container_width=True)

    with col2:
        # Plot temperature as a gauge meter
        temp_value = df_dirty["temperature"].iloc[-1]
        thermostat_fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=temp_value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Temperature (°C)"},
            gauge={'axis': {'range': [0, 60], 'tickmode': 'linear', 'tick0': 0, 'dtick': 10, 'tickwidth': 1,
                            'tickcolor': 'darkgray'},
                   'bar': {'color': 'blue'},
                   'steps': [{'range': [0, 30], 'color': "#81D4FA"},
                             {'range': [30, 60], 'color': "#FFB74D"}],
                   'threshold': {'line': {'color': "black", 'width': 4},
                                 'thickness': 0.75, 'value': temp_value}},
        ))

        thermostat_fig.update_layout(height=400, margin=dict(t=5, b=5, l=20, r=20))
        st.plotly_chart(thermostat_fig, use_container_width=True)

    with col3:
        # show last flow rate and pressure data as single values
        last_row_dirty = df_dirty.iloc[-1]
        st.markdown("### ")  # to add vertical space for better visual only
        #st.metric(label="Pressure (bar)", value=f"{last_row_dirty['pressure']:.2f}")
        st.metric(label="Flow Rate (L/min)", value=f"{last_row_dirty['flow']:.2f}")
        style_metric_cards(background_color="#000000", border_left_color="#d6d6d6")

    # Plot other charts

    st.subheader("TDS")
    tds_fig = px.area(df_dirty, x="timestamp", y="TDS", title="TDS (mg/L)")
    tds_fig.update_traces(line_color='deeppink')
    st.plotly_chart(tds_fig, use_container_width=True)

    #st.subheader("Conductivity")
    #st.plotly_chart(px.line(df_dirty, x="timestamp", y="conductivity", title="Conductivity (µS/cm)"),
     #               use_container_width=True)

    st.subheader("Turbidity")
    tur_fig = px.line(df_dirty, x="timestamp", y="turbidity", title="Turbidity (NTU)")
    tur_fig.update_traces(line=dict(color='mediumorchid'))
    st.plotly_chart(tur_fig, use_container_width=True)


elif view_options == 'System Maintenance':
    st.subheader("🛠️ Predictive Maintenance")
    st.info("This section shows predictive system maintenance data")









