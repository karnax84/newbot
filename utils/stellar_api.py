import yaml
from datetime import datetime
from stellar_sdk import Server, Asset
import pytz

from utils.time_conversions import convert_time_to_utc

# Set up logging configuration
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_asset(asset_code:str="VELO") -> Asset:
    """
    Fetch an Asset object from the asset code based on 'config/config.yaml'.

    Parameters:
    - asset_code: Code of the asset (e.g., "XLM", "USDC")

    Returns:
    - An Asset object corresponding to the given asset code
    """
    # Load configuration
    with open("config/config.yaml", "r") as file:
        config = yaml.safe_load(file)

    return Asset.native() if asset_code == "XLM" else Asset(asset_code, config['asset_issuers'].get(asset_code))


def fetch_last_trade_list(
        base_asset_code:str="VELO",
        counter_asset_code:str="XLM",
        num_trades:int=500
) -> list[dict]:
    """
    Fetch a given number of historical trade data from Stellar Horizon API.

    Parameters:
    - base_asset_code: Base asset code (e.g., "VELO")
    - counter_asset_code: Counter asset code (e.g., "XLM")
    - num_trades: Number of last trades to fetch

    Returns:
    - List of dictionaries containing trade data
    """
    server = Server("https://horizon.stellar.org")

    logging.info(f"Fetching last {num_trades} trades for pair: {base_asset_code}/{counter_asset_code}")

    # Define base and counter assets
    base_asset = get_asset(base_asset_code)
    counter_asset = get_asset(counter_asset_code)

    try:
        all_trade_list = []
        cursor = None

        while len(all_trade_list) < num_trades:
            # Fetch up to 200 trades per request (API limit)
            trades_request = server.trades().for_asset_pair(base=base_asset, counter=counter_asset).order(desc=True).limit(200)
            if cursor:
                trades_request = trades_request.cursor(cursor)

            trades = trades_request.call()

            all_trade_list.extend(trades['_embedded']['records'])

            if len(trades['_embedded']['records']) < 200:
                break  # Stop if fewer than 200 trades are returned

            cursor = trades['_embedded']['records'][-1]['paging_token']  # Update the cursor for the next request

        return all_trade_list[:num_trades]

    except Exception as e:
        logging.error(f"Error fetching trade data: {e}")
        return []


def fetch_new_trade_list(
        base_asset_code: str,
        counter_asset_code: str,
        prior_fetch_time: datetime
) -> list[dict]:
    """
    Fetch historical trade data from Stellar Horizon API after the prior fetch time.

    Parameters:
    - base_asset_code: Base asset code (e.g., "VELO")
    - counter_asset_code: Counter asset code (e.g., "XLM")
    - prior_fetch_time: The last fetch time to get trades after that timestamp

    Returns:
    - List of dictionaries containing new trade data
    """
    server = Server("https://horizon.stellar.org")

    logging.info(f"Fetching new trades for pair: {base_asset_code}/{counter_asset_code} after {prior_fetch_time}")

    # Define base and counter assets
    base_asset = get_asset(base_asset_code)
    counter_asset = get_asset(counter_asset_code)

    try:
        all_trade_list = []
        cursor = None

        while True:
            # Fetch up to 200 trades per request (API limit)
            trades_request = server.trades().for_asset_pair(base=base_asset, counter=counter_asset).order(desc=True).limit(200)
            if cursor:
                trades_request = trades_request.cursor(cursor)

            trades = trades_request.call()

            # Loop through the fetched trades
            for trade in trades['_embedded']['records']:
                trade_time = convert_time_to_utc(trade['ledger_close_time'])

                # Only include trades that occurred after the prior_fetch_time
                if trade_time > prior_fetch_time:
                    all_trade_list.append(trade)
                else:
                    return all_trade_list  # Stop if trade is older than prior_fetch_time

            if len(trades['_embedded']['records']) < 200:
                break  # Stop fetching if fewer than 200 trades are returned

            cursor = trades['_embedded']['records'][-1]['paging_token']  # Update the cursor for the next request

        logging.info(f"Fetched {len(all_trade_list)} new trades after {prior_fetch_time}.")
        return all_trade_list

    except Exception as e:
        logging.error(f"Error fetching new trade data: {e}")
        return []
