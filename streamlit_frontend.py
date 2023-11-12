# -*- coding: utf-8 -*-
"""
Created on Thu Apr 27 19:58:00 2023

@author: Diego
"""

import altair as alt
import datetime as dt
import yfinance as yf
import streamlit as st

from LSPort import *

st.set_page_config(
    page_title = "L/S Pair Analyzer & Backtesting",
    layout = "wide")

st.header("L/S Pair Analyzer & Backtesting")
st.write("Made by Diego Alvarez")

# helper functions
def bus_day_subtract(date_input):

    if dt.date.weekday(date_input) == 6: date_out = date_input - dt.timedelta(days = 6)
    if dt.date.weekday(date_input) == 5: date_out = date_input - dt.timedelta(days =  5)
    else: date_out = date_input - dt.timedelta(days = 7)

    return date_out

# cache functions
@st.cache_data
def _yf_finance(ticker, start, end):

    return(yf.download(
        tickers = ticker,
        start = start,
        end = end)
        [["Adj Close"]])

# parametrized function on the call-side so that the data is cached
@st.cache_data
def position_rebalance(
    _ls_port_obj,
    lookback_window: int,
    rebalance_method: str,
    backtest_start_date: dt.date,
    backtest_end_date: dt.date):

    df_position, df_port = _ls_port_obj.position_rebalance(
        lookback_window = lookback_window,
        rebalance_method = "daily",
        backtest_start_date = backtest_start_date,
        backtest_end_date = backtest_end_date)
    
    return(df_position, df_port)

@st.cache_data
def plot_position_rebalance(
    _ls_port_obj,
    df_position: pd.DataFrame,
    df_port: pd.DataFrame,
    lookback_window: int,
    rebalance_method: str,
    figsize: tuple = (28,6)):

    fig_weighted, fig_port = _ls_port_obj._plot_position_rebalance(
        df_position = df_position,
        df_port = df_port,
        lookback_window = lookback_window,
        rebalance_method = rebalance_method,
        figsize = figsize)
    
    return fig_weighted, fig_port

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
        set_index("Date"))
    
    st.write("Historical Returns from {} to {}".format(
        df_input_full.index.min().date(),
        df_input_full.index.max().date()))
    
    cum_rtns = ((np.cumprod(df_input_full.pct_change() + 1) - 1) * 100).reset_index().melt(id_vars = "Date")
    cum_rtn_chart = (alt.Chart(
        data = cum_rtns).
        mark_line().
        encode(
            x = "Date",
            y = alt.Y(shorthand = "value", title = "Cumulative Returns (%)"),
            color = "variable").
        properties(
            width = 1_000,
            height = 400))
    
    st.altair_chart(cum_rtn_chart)
    
    df_input_drop = df_input_full.dropna()
    if len(df_input_drop) != len(df_input_full):
        df_input = df_input_drop
        st.write("{} Days Missing and were dropped".format(
            len(df_input_full) - len(df_input_drop)))
        
    else:
        df_input = df_input_full

    ls_port = LSPort(
        long_position = df_input_full[long_leg],
        short_position = df_input_full[short_leg],
        benchmark = df_input_full[benchmark_leg])
    
    sidebar_options = st.sidebar.selectbox(
        label = "Options",
        options = ["backtest"])
    
    col1, col2, col3 = st.columns(3)
    if sidebar_options == "backtest":

        plotting_options = st.sidebar.selectbox(
            label = "Plotting Option",
            options = ["MatplotLib", "Streamlit"])

        with col1:

            rebalance_period = st.selectbox(
                label = "rebalance",
                options = ["daily"])
            
            lookback_window = st.number_input(
                label = "Rolling Beta Window",
                min_value = 1,
                max_value = 365 * 2,
                value = 120)
            
        with col2:

            min_value = df_benchmark.index.min() + dt.timedelta(days = lookback_window)
            max_value = df_benchmark.index.max()

            backtest_start_date = st.date_input(
                label = "Backtest Start Date",
                value = min_value,
                min_value = min_value,
                max_value = max_value)
    
            backtest_end_date = st.date_input(
                label = "Backtest End Date",
                value = max_value,
                min_value = min_value,
                max_value = max_value)
            
            if backtest_start_date > backtest_end_date: st.write("Start Date Needs to be before End Date")       

        with col3:

            backtest_run_button = st.radio(
                label = "Run Button",
                options = ["Stop", "Run"])
            
        if backtest_run_button == "Run":

            df_position, df_port = position_rebalance(
                _ls_port_obj = ls_port,
                lookback_window = lookback_window,
                rebalance_method = rebalance_period,
                backtest_start_date = backtest_start_date,
                backtest_end_date = backtest_end_date)
            
            if plotting_options == "MatplotLib":
                
                fig_weighted, fig_port = plot_position_rebalance(
                        _ls_port_obj = ls_port,
                        df_position = df_position,
                        df_port = df_port,
                        lookback_window = lookback_window,
                        rebalance_method = rebalance_period)
                
                st.pyplot(fig_weighted)
                st.pyplot(fig_port)

            if plotting_options == "Streamlit":

                st.subheader("Long: {} Short: {} Benchmark: {} {} rolling OLS rebalance: {} from {} to {}".format(
                    ls_port.long_name,
                    ls_port.short_name,
                    ls_port.benchmark_name,
                    lookback_window,
                    rebalance_period,
                    df_position.Date.min().date(),
                    df_position.Date.max().date()))
                
                plot_col1, plot_col2 = st.columns(2)

                with plot_col1:

                    df_tmp = (df_position.query(
                        "position == 'long'")
                        [["Date", "lag_weight"]].
                        assign(
                            lag_weight = lambda x: x.lag_weight * 100,
                            short = lambda x: 100 - x.lag_weight).
                        rename(columns = {
                            "lag_weight": ls_port.long_name,
                            "short": ls_port.short_name}).
                        dropna().
                        melt(id_vars = "Date", var_name = "position", value_name = "weight"))
                
                    plot = (alt.Chart(
                        data = df_tmp).
                        mark_area().
                        encode(
                            x = "Date",
                            y = alt.Y(
                                shorthand = "weight", 
                                title = "Weighting (%)",
                                scale = alt.Scale(domain = [0,100])),
                            color = "position").
                        properties(
                            width = 700,
                            height = 300))
                    
                    st.write("Portfolio Weighting")
                    st.altair_chart(plot)

                with plot_col2:

                    df_beta = (df_position.query(
                        "position == ['long', 'short']")
                        [["Date", "position", "weighted_directional_beta"]].
                        pivot(index = "Date", columns = "position", values = "weighted_directional_beta").
                        reset_index())
                    
                    line_chart1 = (alt.Chart(
                        data = df_beta).
                        mark_line().
                        encode(
                            x = "Date",
                            color = alt.value("#ff0000"),
                            y = alt.Y(
                                shorthand = "long",
                                title = "Long β",
                                scale = alt.Scale(domain = [
                                    df_beta["long"].min(),
                                    df_beta["long"].max()]))))
                    
                    line_chart2 = (alt.Chart(
                        data = df_beta).
                        mark_line().
                        encode(
                            x = "Date",
                            y = alt.Y(
                                shorthand = "short",
                                title = "Short β", 
                                scale = alt.Scale(
                                    reverse = True,
                                    domain = [
                                        df_beta["short"].min(),
                                        df_beta["short"].max()]))))
                    
                    combined_chart = (alt.layer(
                        line_chart1, line_chart2).
                        resolve_scale(y = "independent").
                        properties(
                            width = 700,
                            height = 300))

                    st.write("Weighted Beta Matching")
                    st.altair_chart(combined_chart)

                plot_col3, plot_col4, plot_col5 = st.columns(spec = 3)

                with plot_col3:

                    df_port_beta = (df_position[
                        ["Date", "ticker", "weighted_directional_beta"]].
                        pivot(index = "Date", columns = "ticker", values = "weighted_directional_beta").
                        sum(axis = 1).
                        to_frame().
                        rename(columns = {0: "Beta"}).
                        reset_index())
                    
                    st.write("Portfolio Beta")
                    beta_chart = (alt.Chart(
                        data = df_port_beta).
                        mark_line().
                        encode(
                            x = "Date",
                            y = alt.Y(
                                shorthand = "Beta",
                                title = "Beta",
                                scale = alt.Scale(domain = [
                                    df_port_beta["Beta"].min(),
                                    df_port_beta["Beta"].max()]))).
                        properties(
                            width = 450,
                            height = 300))
                    
                    st.altair_chart(beta_chart)

                with plot_col4:

                    position_cum_plot = (alt.Chart(
                        data = df_position.rename(columns = {"cum_rtn": "Cumulative Return"})).
                        mark_line().
                        encode(
                            x = "Date",
                            y = "Cumulative Return",
                            color = "ticker").
                        properties(
                            width = 450,
                            height = 300))
                    
                    st.write("Individual Position Performance")
                    st.altair_chart(position_cum_plot)

                with plot_col5:

                    df_direction = (pd.DataFrame({
                        "position": ["long", "short"],
                        "direction": [1, -1]}))

                    df_port_rtns = (df_position[
                        ["Date", "ticker", "weighted_rtn", "position"]].
                        merge(right = df_direction, how = "inner", on = ["position"]).
                        assign(weighted_rtn = lambda x: x.weighted_rtn * x.direction).
                        drop(columns = ["position"]).
                        pivot(index = "Date", columns = "ticker", values = "weighted_rtn").
                        sum(axis = 1).
                        to_frame().
                        rename(columns = {0: "Cumulative Return (%)"}))
                    
                    df_port_cum_rtn = ((np.cumprod(1 + df_port_rtns) - 1) * 100).reset_index()
                    cum_plot = (alt.Chart(
                        data = df_port_cum_rtn).
                        mark_line().
                        encode(
                            x = "Date",
                            y = "Cumulative Return (%)").
                        properties(
                            width = 450,
                            height = 300))
                    
                    st.write("Portfolio Performance")
                    st.altair_chart(cum_plot)