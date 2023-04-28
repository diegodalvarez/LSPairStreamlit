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

col1, col2, col3 = st.columns(3)

with col1: 
    st.subheader("Input Data")
    st.write("SPX has the ticker ^GSPC in Yahoo")

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
        max_value = 100)
    ratio = ratio / 100

col1, col2, col3 = st.columns(3)

with col1 : 
    
    long_leg = st.text_input("Long Leg (Ticker)")
    if run_button == "Run":
    
        try:
            
            df_long = (yf.download(
                tickers = long_leg,
                start = start_date,
                end = end_date)
                [["Adj Close"]].
                rename(columns = {"Adj Close": long_leg}))
            
            st.write(df_long.head(5))
            
        except: 
            st.write("There was a problem collecting the data from Yahoo")
        
with col2: 
    
    short_leg = st.text_input("Short Leg")
    if run_button == "Run":
    
        try:
            
            df_short = (yf.download(
                tickers = short_leg,
                start = start_date,
                end = end_date)
                [["Adj Close"]].
                rename(columns = {"Adj Close": short_leg}))
            
            st.write(df_short.head(5))
            
        except: 
            st.write("There was a problem collecting the data from Yahoo")
    
with col3: 
    
    benchmark_leg = st.text_input("Benchmark")
    if run_button == "Run":
    
        try:
            df_benchmark = (yf.download(
                tickers = benchmark_leg,
                start = start_date,
                end = end_date)
                [["Adj Close"]].
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
        options = ["Regression Results", "Individual Premias", "Even Rebalance"])
    
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
            
            
    
            