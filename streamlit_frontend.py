# -*- coding: utf-8 -*-
"""
Created on Thu Apr 27 19:58:00 2023

@author: Diego
"""

import datetime as dt
import yfinance as yf
import streamlit as st

from LSPairStreamlit import *

st.set_page_config(
    page_title = "L/S Pair Analyzer",
    layout = "wide")

st.header("Long Short Pair Analyzer")
st.write("Made by Diego Alvarez")

bad_tickers = {
    "SPX": "^GSPC",
    "MOVE": "^MOVE",
    "VIX": "^VIX",
    "^DJI": "DJI",
    "^IXIC": "IXIC",
    "^RUT": "RUT"}

col1, col2, col3 = st.columns(3)

with col1: 
    st.subheader("Input Data")

    st.write("All Prices Include Dividends and Stock Splits")

with col2:
    
    today_date = dt.date.today()
    
    start_date = st.date_input(
        label = "Start Date",
        value = dt.date(today_date.year - 5, today_date.month, today_date.day))
    
    end_date = st.date_input(
        label = "End Date",
        value = today_date)
    
with col3: 
    
    run_button = st.radio(
        label = "Select Run to extract data",
        options = ["Stop", "Run"])
    
    ratio = st.number_input(
        label = "In-Sample Ratio (Expressed as Percentage)",
        min_value = 1,
        max_value = 100,
        value = 70)
    ratio = ratio / 100

@st.cache_data
def _yf_finance(ticker, start, end):

    return(yf.download(
        tickers = ticker,
        start = start,
        end = end)
        [["Adj Close"]])

col1, col2, col3 = st.columns(3)

with col1 : 
    
    long_leg = st.text_input("Long Leg (Ticker)").upper()
    try: long_leg = bad_tickers[long_leg]
    except: pass

    if run_button == "Run":
    
        try:

            df_long = (_yf_finance(
                ticker = long_leg,
                start = start_date,
                end = end_date).
                rename(columns = {"Adj Close": long_leg}))
            
            st.write(df_long.head(5))
            
        except: 
            st.write("There was a problem collecting the data from Yahoo")
        
with col2: 
    
    short_leg = st.text_input("Short Leg").upper()
    try: short_leg = bad_tickers[short_leg]
    except: pass

    if run_button == "Run":
    
        try:
            
            df_short = (_yf_finance(
                ticker = short_leg,
                start = start_date,
                end = end_date).
                rename(columns = {"Adj Close": short_leg}))
            
            st.write(df_short.head(5))
            
        except: 
            st.write("There was a problem collecting the data from Yahoo")
    
with col3: 
    
    benchmark_leg = st.text_input("Benchmark").upper()
    try: benchmark_leg = bad_tickers[benchmark_leg]
    except: pass

    if run_button == "Run":
    
        try:
            df_benchmark = (_yf_finance(
                ticker = benchmark_leg,
                start = start_date,
                end = end_date).
                rename(columns = {"Adj Close": benchmark_leg}))
            
            st.write(df_benchmark.head(5))
            
        except: 
            st.write("There was a problem collecting the data from Yahoo")
            
if run_button == "Run":
    
    df_input_full = (df_long.reset_index().merge(
        df_short.reset_index(),
        how = "outer",
        on = ["Date"]).
        merge(
            df_benchmark.reset_index(),
            how = "outer",
            on = ["Date"]).
        set_index("Date").
        pct_change())
    
    df_input_drop = df_input_full.dropna()
    if len(df_input_drop) != len(df_input_full):
        df_input = df_input_drop
        st.write("{} Days Missing and were dropped".format(
            len(df_input_full) - len(df_input_drop)))
        
    else:
        df_input = df_input_full
        
    ls_pair = LSPairStreamlit(
        long_position = df_input[df_input.columns[0]],
        short_position = df_input[df_input.columns[1]],
        benchmark = df_input[df_input.columns[2]],
        in_sample_ratio = ratio)
        
    sidebar_options = st.sidebar.selectbox(
        label = "Options",
        options = ["Regression Results", "Individual Premias", "Even Rebalance", "Rolling OLS"])
    
    if sidebar_options == "Regression Results":
        
        sample_set_options = st.sidebar.selectbox(
            label = "Sample Set", 
            options = ["In-Sample", "Out-of-Sample", "Full-Sample", "All"])
        
        if sample_set_options == "In-Sample":
            
            col1, col2 = st.columns(2)
            with col1:st.write(ls_pair.in_sample_long_lm_res)
            with col2:st.write(ls_pair.in_sample_short_lm_res)
            st.pyplot(ls_pair.plot_regress())
            
        if sample_set_options == "Out-of-Sample":
            
            col1, col2 = st.columns(2)
            with col1: st.write(ls_pair.out_sample_long_lm_res)
            with col2: st.write(ls_pair.out_sample_short_lm_res)
            st.pyplot(ls_pair.plot_out_regress())
            
        if sample_set_options == "Full-Sample":
            
            col1, col2 = st.columns(2)
            with col1: st.write(ls_pair.full_sample_long_lm_res)
            with col2: st.write(ls_pair.full_sample_short_lm_res)
            st.pyplot(ls_pair.plot_full_regress())
            
            
        if sample_set_options == "All":
            
            st.subheader("In-Sample")
            col1, col2 = st.columns(2)
            with col1:st.write(ls_pair.in_sample_long_lm_res)
            with col2:st.write(ls_pair.in_sample_short_lm_res)
            st.pyplot(ls_pair.plot_regress())
            
            st.subheader("Out-of-Sample")
            col1, col2 = st.columns(2)
            with col1: st.write(ls_pair.out_sample_long_lm_res)
            with col2: st.write(ls_pair.out_sample_short_lm_res)
            st.pyplot(ls_pair.plot_out_regress())
            
            st.subheader("Full-Sample")
            col1, col2 = st.columns(2)
            with col1: st.write(ls_pair.full_sample_long_lm_res)
            with col2: st.write(ls_pair.full_sample_short_lm_res)
            st.pyplot(ls_pair.plot_full_regress())
            
    if sidebar_options == "Individual Premias":
        
        sample_set_options = st.sidebar.selectbox(
            label = "Sample Set", 
            options = ["In-Sample", "Out-of-Sample", "Full-Sample", "All"])
        
        if sample_set_options == "In-Sample":
            st.pyplot(ls_pair.plot_cum())
            
        if sample_set_options == "Out-of-Sample":
            st.pyplot(ls_pair.plot_out_sample_cum())

        if sample_set_options == "Full-Sample":
            st.pyplot(ls_pair.plot_full_sample_cum())
            
        if sample_set_options == "All":
            
            st.subheader("In-Sample")
            st.pyplot(ls_pair.plot_cum())
            st.subheader("Out-of-Sample")
            st.pyplot(ls_pair.plot_out_sample_cum())
            st.subheader("Full-Sample")
            st.pyplot(ls_pair.plot_full_sample_cum())
            
    if sidebar_options == "Even Rebalance":
        
        st.subheader("Rebelanced 50/50 Daily (Not Include Transaction Costs)")
        st.pyplot(ls_pair.generate_even_rebal_risk_premia())
            
    if sidebar_options == "Rolling OLS":

        rolling_ols_options = st.sidebar.selectbox(
            label = "Rolling OLS options",
            options = [
            "Rolling Plot", "Long / Short Parameter Comparison", 
            "Rolling Parameter Correlation", "Parameter Distribution",
            "Rolling Distribution Contour Map"])
        
        if rolling_ols_options == "Rolling Plot":

            col1, col2, col3 = st.columns(3)
            with col1:

                window_input = st.number_input(
                    label = "Window size",
                    min_value = 1,
                    max_value = 252 * 10,
                    value = 30)
                
                confidence_input = st.number_input(
                    label = "Confidence Interval (As Percentage)",
                    min_value = 1,
                    max_value = 100,
                    value = 95)
                
                confidence_input = round(1 - (confidence_input / 100), 2)

                ols_run_button = st.radio(
                    label = "Click Run to start",
                    options = ["Stop", "Run"])
                
            with col2:

                for i in range(11):
                    st.write(" ")

                fill_button = st.radio(
                    label = "Confidence Interval Fill",
                    options = ["Fill", "No Fill"])

            if ols_run_button == "Run":

                if fill_button == "Fill":

                    st.pyplot(ls_pair.plot_single_rolling_ols(
                        window = window_input,
                        conf_int = confidence_input))
                
                if fill_button == "No Fill":

                    st.pyplot(ls_pair.plot_single_rolling_ols(
                        window = window_input,
                        fill = False))
    
        if rolling_ols_options == "Long / Short Parameter Comparison":

            col1, col2, col3 = st.columns(3)

            with col1:

                window_input = st.number_input(
                        label = "Window size",
                        min_value = 1,
                        max_value = 252 * 10,
                        value = 30)
                    
                confidence_input = st.number_input(
                    label = "Confidence Interval (As Percentage)",
                    min_value = 1,
                    max_value = 100,
                    value = 95)
                
                confidence_input = (100 - confidence_input) / 100
                
                ols_run_button = st.radio(
                    label = "Click Run to start",
                    options = ["Stop", "Run"])
                
            with col2:

                for i in range(11):
                    st.write(" ")

                fill_button = st.radio(
                    label = "Confidence Interval Fill",
                    options = ["Fill", "No Fill"])
                
            if ols_run_button == "Run":

                if fill_button == "Fill":

                    st.pyplot(ls_pair.plot_single_rolling_ols_comparison(
                        window = window_input,
                        conf_int = confidence_input))
                    
                if fill_button == "No Fill":

                    st.pyplot(ls_pair.plot_single_rolling_ols_comparison(
                        window = window_input))
                    
        if rolling_ols_options == "Rolling Parameter Correlation":

            col1, col2, col3 = st.columns(3)
            with col1:

                ols_window_input = st.number_input(
                    label = "OLS Window size",
                    min_value = 1,
                    max_value = 252 * 10,
                    value = 30)
                
                run_button = st.radio(
                    label = "Click Run to start",
                    options = ["Stop", "Run"])
                
            with col2: 

                corr_window_input = st.number_input(
                    label = "Correlation Window size",
                    min_value = 1,
                    max_value = 252 * 10,
                    value = 30)
                
            if run_button == "Run":

                st.pyplot(ls_pair.plot_single_rolling_ols_parameter_comparison(
                    ols_window = ols_window_input,
                    corr_window = corr_window_input))

        if rolling_ols_options == "Parameter Distribution":

            col1, col2, col3 = st.columns(3)
            with col1:

                ols_window_input = st.number_input(
                    label = "OLS Window size",
                    min_value = 1,
                    max_value = 252 * 10,
                    value = 30)
                
                run_button = st.radio(
                    label = "Click Run to start",
                    options = ["Stop", "Run"])
                
            if run_button == "Run":

                st.pyplot(ls_pair.plot_single_rolling_ols_hist(
                    ols_window = ols_window_input))
                
        if rolling_ols_options == "Rolling Distribution Contour Map":

            col1, col2, col3 = st.columns(3)
            with col1:

                ols_window_input = st.number_input(
                    label = "OLS Window size",
                    min_value = 1,
                    max_value = 252 * 10,
                    value = 30)
                
                run_button = st.radio(
                    label = "Click Run to start",
                    options = ["Stop", "Run"])
                
            if run_button == "Run":

                st.pyplot(ls_pair.plot_single_rolling_ols_contour(
                    ols_window = ols_window_input))