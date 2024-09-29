import logging
import pandas as pd
import streamlit as st

from utils.time_conversions import convert_time_to_utc, get_time_now_utc
from utils.stellar_api import fetch_last_trade_list, fetch_new_trade_list

# Set up logging configuration
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO  # Set the log level (can be changed to DEBUG for more details)
)

# %% ########################### Define functions to manage trade data list ###########################
import numpy as np  # You need this import to calculate standard deviation


def init_trade_list():
    """Fetch initial trade data and initialize session state."""
    logging.info("Initializing trade list.")
    with st.spinner(f"Fetching initial {st.session_state['num_trade_data']} {st.session_state['base_asset_code']}/{st.session_state['counter_asset_code']} trade data..."):
        try:
            # Fetch the trade data
            trade_list = fetch_last_trade_list(base_asset_code=st.session_state["base_asset_code"],
                                               counter_asset_code=st.session_state["counter_asset_code"],
                                               num_trades=st.session_state["num_trade_data"])
            st.session_state["trade_list"] = trade_list
            logging.info(f"Initial trade data fetched: {len(trade_list)} trades.")

            # Update last trade time
            st.session_state["last_trade_time"] = convert_time_to_utc(st.session_state["trade_list"][0]['ledger_close_time'])
            logging.info(f"Last trade time: {st.session_state['last_trade_time']}")

            prices = [float(trade['price']['n']) / float(trade['price']['d']) for trade in st.session_state["trade_list"]]
            st.session_state["min_price"] = min(prices)            # Calculate the minimum price based on the updated trade list
            # logging.info(f"Initial minimum price: {st.session_state['min_price']}")
            st.session_state["mean_price"] = np.mean(prices)            # Calculate the mean price
            # logging.info(f"Initial mean price: {st.session_state['mean_price']}")
            st.session_state["price_std_dev"] = np.std(prices)            # Calculate the price standard deviation
            # logging.info(f"Initial price standard deviation: {st.session_state['price_std_dev']}")

        except Exception as e:
            logging.error(f"Error fetching initial trade data: {e}")


def update_trade_list():
    """Fetch new trade data and update session state."""
    # logging.info("Updating trade list.")
    try:
        new_trade_list = fetch_new_trade_list(base_asset_code=st.session_state["base_asset_code"],
                                              counter_asset_code=st.session_state["counter_asset_code"],
                                              prior_fetch_time=st.session_state["last_trade_time"])
        if new_trade_list:
            logging.info(f"Fetched {len(new_trade_list)} new trades.")
            st.session_state["new_trade_list"] = new_trade_list
            st.session_state["trade_list"] = new_trade_list + st.session_state["trade_list"]
            st.session_state["trade_list"] = st.session_state["trade_list"][:st.session_state["num_trade_data"]]

            # Update last trade time
            st.session_state["last_trade_time"] = convert_time_to_utc(st.session_state["trade_list"][0]['ledger_close_time'])
            logging.info(f"Last trade time: {st.session_state['last_trade_time']}")

            # Calculate prices and volumes
            prices = [float(trade['price']['n']) / float(trade['price']['d']) for trade in st.session_state["trade_list"]]
            volumes = [float(trade['base_amount']) for trade in st.session_state["trade_list"]]

            st.session_state["min_price"] = min(prices)            # Recalculate the minimum price based on the updated trade list
            # logging.info(f"Updated minimum price: {st.session_state['min_price']}")

            st.session_state["mean_price"] = np.mean(prices)            # Calculate the mean price
            # st.session_state["mean_price"] = np.average(prices, weights=volumes)            # Calculate updated volume-weighted mean price
            # logging.info(f"Updated mean price: {st.session_state['mean_price']}")

            st.session_state["price_std_dev"] = np.std(prices)            # Calculate the price standard deviation
            # mean_price = st.session_state["mean_price"]
            # weighted_variance = np.average((np.array(prices) - mean_price) ** 2, weights=volumes)# Calculate updated volume-weighted standard deviation of prices
            # st.session_state["price_std_dev"] = np.sqrt(weighted_variance)
            # logging.info(f"Updated price standard deviation: {st.session_state['price_std_dev']}")

        else:
            st.session_state["new_trade_list"] = []
            logging.info("No new trades found.")

    except Exception as e:
        logging.error(f"Error updating trade list: {e}")


# %% ########################### Define a function to convert trade data to DataFrame ###########################
def update_trade_df(): 
    # logging.info(f"Updating trade dataframe to be displayed.")
    trade_list = st.session_state["trade_list"]
    trade_data = []
    for trade in trade_list:
        try:
            # Convert timestamp to UTC and then to the machine's local timezone
            timestamp_utc = convert_time_to_utc(trade['ledger_close_time'])
            price = float(trade['price']['n']) / float(trade['price']['d'])
            amount = float(trade.get('base_amount', 0))
            trade_data.append({'timestamp': timestamp_utc, 
                               'price': price, 
                               'volume': amount})
        except KeyError as e:
            logging.warning(f"Missing key {e} in trade: {trade}")
        except ValueError as e:
            logging.error(f"Data conversion error: {e} in trade: {trade}")

    if not trade_data:
        logging.info("No valid trades to process.")
        return pd.DataFrame(columns=['timestamp', 
                                     'price', 
                                     'volume'])

    # Create the DataFrame
    df = pd.DataFrame(trade_data)
    df.set_index('timestamp', inplace=True)
    # If timestamps are duplicated, sum the volume and take a mean for the price
    df = df.groupby('timestamp').agg({'price': 'mean',
                                      'volume': 'sum'})
    df['timestamp'] = df.index  # Keep 'timestamp' as both index and column
    df.sort_index(inplace=True)
    
    # logging.info("Inserting current time price.")
    time_now_utc = get_time_now_utc() # Ensure this is in UTC
    current_price = df['price'].iloc[-1]
    df_now = pd.DataFrame([{'timestamp': time_now_utc,
                            'price': current_price,
                            'volume': 0.0}])

    st.session_state['trade_df'] = pd.concat([df, df_now])
    # logging.info(f"{len(trade_list)} trade data successfully converted to DataFrame, with overlapping timestamps handled.")
    
    st.session_state["current_price"] = current_price
    # logging.info(f"Current price: {current_price}")

    st.session_state["last_update_time"] = time_now_utc
    # logging.info(f"Last update time: {st.session_state['last_update_time']}")

