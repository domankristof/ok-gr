#Data Analysis Functions -- Lap time calculations, sector analysis, performance metrics
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

weather_df = pd.read_csv('/Users/kristof/Downloads/virginia-international-raceway/VIR/Race 1/26_Weather_Race 1_Anonymized.CSV')

#Weather Data Plotting Function
def weather_plot(weather_df):
    #UTC to time conversion
    weather_df['Time'] = pd.to_datetime(weather_df['TIME_UTC_SECONDS'], unit = 's', utc=True)

    st.write(weather_df['Time'].head())