import streamlit as st
from data_utils import healthy_drinkable_water_ranges
import matplotlib.pyplot as plt
import base64
from io import BytesIO

# create function to help style the average metrics when needed
# this will help us indicate an alert when values are above drinkable ranges
def metric_color(value, parameter):

    healthy_ranges = healthy_drinkable_water_ranges()
    min_val, max_val = healthy_ranges[parameter]

    return "green" if min_val <= value <= max_val else "red"

def metric_style(label, value, unit, color):
    html = f"""
        <div style="background-color: white; border: 1px solid black; border-radius: 8px;
                    padding: 1rem; margin-bottom: 0.8rem; text-align: center;">
            <h5 style="margin: 0; color: black;">{label}</h5>
            <h3 style="margin: 0; color: {color};">{value} {unit}</h3>
        </div>
        """
    st.markdown(html, unsafe_allow_html=True)


def metric_style_(label, value, unit, color, trend_data):

    # Create sparkline as a base64 image
    fig, ax = plt.subplots(figsize=(2, 0.6), dpi=100)
    ax.plot(trend_data, color=color, linewidth=2)
    ax.axis("off")
    fig.patch.set_alpha(0)  # transparent background
    ax.set_facecolor("white")  # background white

    buffer = BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0, transparent=True)
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)

    html = f"""
            <div style="background-color: white; border: 1px solid black; border-radius: 8px;
                        padding: 1rem; margin-bottom: 0.8rem; text-align: center;
                        background-image: url('data:image/png;base64,{img_base64}');
                        background-repeat: no-repeat;
                        background-position: center bottom;
                        background-size: 90% 40px;">
                <h5 style="margin: 0; color: black;">{label}</h5>
                <h3 style="margin: 0; color: {color};">{value} {unit}</h3>
            </div>
        """
    st.markdown(html, unsafe_allow_html=True)
