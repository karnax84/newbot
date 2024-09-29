import time
import yaml
import pandas as pd
import streamlit as st
from datetime import datetime

# %%
# Load configuration from YAML file
with open("config/config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

# Initialize session state values if not already set
print("*******************************************************************")
for key, default in [("base_asset_code", ""), 
                     ("counter_asset_code", ""),
                     ("num_trade_data", 1000),
                     ("trading_capital_percent", 1),
                     ("price_interval_percent", 1),
                     ("stellar_key", ""),
                     ("balances", None),
                     ("min_price", 10000),
                     ("mean_price", 0),
                     ("price_std_dev", 0),
                     ("current_price", 0),
                     ("trade_list", []),
                     ("new_trade_list", []),
                     ("exchanges_list", []),
                     ("trade_df", pd.DataFrame()),
                     ("last_trade_time", datetime.now()),
                     ("last_update_time", datetime.now()),
                     ("algo_active", False),
                     ]:
    if key not in st.session_state:
        st.session_state[key] = default

from app_data import *
from app_draw import *
from engine.trading_bot import TradingBot

# Set page configuration
st.set_page_config(page_title="Stellar Auto Trader", layout="wide")

# Sidebar
st.sidebar.image("assets/logo.jpg", use_column_width=True)
st.sidebar.title("Stellar Auto Trader")


# %% Main page layout
col1, col2 = st.columns([3, 1])

with col1:
    # Asset pair selection
    col11, col12 = st.columns([1, 1])
    with col11:
        base_asset_options = ["VELO", "SHX"]
        base_asset_code = st.selectbox("**Base Asset**", 
                                       base_asset_options,
                                       disabled=st.session_state['algo_active'])
        base_asset_balance_placeholder = st.empty()

    with col12:
        counter_asset_options = ["XLM"]
        counter_asset_code = st.selectbox("**Counter Asset**", 
                                          counter_asset_options,
                                          disabled=st.session_state['algo_active'])
        counter_asset_balance_placeholder = st.empty()

    chart_placeholder = st.empty()

    # _, col13, col14 = st.columns([2,2,2])
    # with col13:
    #     # Number of trade data to consider
    #     num_trade_data = st.slider("Number of Trade Data to Consider", 
    #                                 min_value=100, 
    #                                 max_value=1000, 
    #                                 value=500, 
    #                                 step=100,
    #                                 disabled=st.session_state['algo_active'])
    #     # if num_trade_data != st.session_state["num_trade_data"]:
    #     #     st.session_state["num_trade_data"] = num_trade_data
    #     #     st.rerun()
        
with col2:
    account_balance_placeholder = st.empty()
    trading_actions_placeholder = st.empty()


# %%
# When Stellar key is input/changed
stellar_key = st.sidebar.text_input("Enter Your Stellar Key (Private)", 
                                    type="password", 
                                    disabled=st.session_state['algo_active'])

# Number of trade data to consider
if stellar_key:
    trading_capital_percent = st.sidebar.slider("Trading Capital XLM Percent [%]", 
                                min_value=1, 
                                max_value=10, 
                                value=1, 
                                step=1,
                                disabled=st.session_state['algo_active'])
    price_interval_percent = st.sidebar.slider("Price Interval Percent [%]", 
                                min_value=1, 
                                max_value=10, 
                                value=1, 
                                step=1,
                                disabled=st.session_state['algo_active'])
    # if num_trade_data != st.session_state["num_trade_data"]:
    #     st.session_state["num_trade_data"] = num_trade_data
    #     st.rerun()

def apply_settings():
    st.session_state["stellar_key"] = stellar_key
    st.session_state["base_asset_code"] = base_asset_code
    st.session_state["counter_asset_code"] = counter_asset_code
    # st.session_state["num_trade_data"] = num_trade_data
 
# Toggleable trading control
if stellar_key:
    if st.session_state["algo_active"]:
        if st.sidebar.button("Stop Bot Action", use_container_width=True):
            st.session_state["algo_active"] = False
            apply_settings()
            st.rerun()
    else:
        if st.sidebar.button("Start Bot Action", use_container_width=True):
            st.session_state["algo_active"] = True
            apply_settings()
            st.rerun()


# %% Initialize when start or rerun
bot = TradingBot(base_asset_code=st.session_state['base_asset_code'],
                 counter_asset_code=st.session_state['counter_asset_code'])
if stellar_key:
    bot.set_account(stellar_key=stellar_key,
                    trading_capital_percent=st.session_state["trading_capital_percent"],
                    price_interval_percent=st.session_state["price_interval_percent"])

# %% Cotinuously updating
while True:
    if stellar_key and stellar_key != st.session_state["stellar_key"]:
        st.session_state["stellar_key"] = stellar_key
        bot.set_account(stellar_key=stellar_key,
                        trading_capital_percent=st.session_state["trading_capital_percent"],
                        price_interval_percent=st.session_state["price_interval_percent"])
        st.session_state['balances'] = bot.balances
        # st.session_state["balances"] = None

    if base_asset_code != st.session_state["base_asset_code"]:
        st.session_state["base_asset_code"] = base_asset_code
        init_trade_list()
    if counter_asset_code != st.session_state["counter_asset_code"]:
        st.session_state["counter_asset_code"] = counter_asset_code
        init_trade_list()

    # Update balances
    if stellar_key:
        # bot.set_account(stellar_key=stellar_key)
        with base_asset_balance_placeholder.container():
            write_asset_balance(st.session_state["base_asset_code"])
        with counter_asset_balance_placeholder.container():
            write_asset_balance(st.session_state["counter_asset_code"])
        
        with account_balance_placeholder.container():
            account_balance_table()
    
        if trading_capital_percent != st.session_state["trading_capital_percent"]:
            st.session_state["trading_capital_percent"] = trading_capital_percent
            init_trade_list()

        if price_interval_percent != st.session_state["price_interval_percent"]:
            st.session_state["price_interval_percent"] = price_interval_percent
            init_trade_list()

    # if num_trade_data != st.session_state["num_trade_data"]:
    #     st.session_state["num_trade_data"] = num_trade_data
    #     init_trade_list()
    
    # Update trades
    update_trade_list()
    update_trade_df()
    with chart_placeholder.container():
        draw_chart()

    if stellar_key and st.session_state['algo_active']:
        bot.do_exchange(current_price=st.session_state["current_price"],
                        mean_price=st.session_state["mean_price"],
                        price_std_dev=st.session_state["price_std_dev"])
        st.session_state['exchanges_list'] = bot.exchanges

        st.session_state['balances'] = bot.get_all_balances()

        print(bot.exchanges)
        with trading_actions_placeholder.container():
            trading_actions_table()

    time.sleep(1)


# %%
