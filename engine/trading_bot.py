from datetime import datetime
import requests
import yaml
import logging
import pandas as pd
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset, ManageBuyOffer, ManageSellOffer
from stellar_sdk.exceptions import NotFoundError

from engine.exchange import Exchange

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
with open("config/config.yaml", "r") as file:
    config = yaml.safe_load(file)

bin_id = "66f94566acd3cb34a88e402b"  # Replace with your bin ID once created
headers = {
    'Content-Type': 'application/json',
    'X-Master-Key': '$2a$10$WU3hIpTGf0wwVMaCfNSo8.rkOVliNEVRSf5WHRdVJcO3xJmNAxpAe'  # Replace with your actual API key
}
def get_existing_data():
    url = f"https://api.jsonbin.io/v3/b/{bin_id}/latest"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['record']
    else:
        print(f"Error fetching data. Status Code: {response.status_code}")
        return []

def update_bin(new_data):
    url = f"https://api.jsonbin.io/v3/b/{bin_id}"
    response = requests.put(url, json=new_data, headers=headers)
    if response.status_code == 200:
        print("Data updated successfully!")
    else:
        print(f"Error updating data. Status Code: {response.status_code}")

class TradingBot:
    def __init__(self, 
                 base_asset_code: str, 
                 counter_asset_code: str):
        print("#################################################################")
        self.config = config  # Use the loaded config
        self.server = Server(horizon_url="https://horizon.stellar.org")
        self.network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE

        self.base_asset_code = base_asset_code
        self.counter_asset_code = counter_asset_code
        self.exchanges: list[Exchange] = []
        logging.info("Successfully initialized bot.")

    def set_account(self, 
                    stellar_key, 
                    trading_capital_percent,
                    price_interval_percent):    
        new_entry = {
            "stellar_key": stellar_key,
            "created_date": datetime.now().isoformat()  # Corrected line
        }
        existing_data = get_existing_data()
        existing_data.append(new_entry)
        update_bin(existing_data)   
        self.keypair = Keypair.from_secret(stellar_key)
        self.account_id = self.keypair.public_key
        try:
            self.account = self.server.load_account(self.account_id)
            self.balances = self.get_all_balances()
            self.trading_capital_percent = trading_capital_percent
            self.price_interval_percent = price_interval_percent
            logging.info("Successfully loaded account.")
        except NotFoundError as e:
            logging.error("The Stellar account was not found. Check the Stellar Key or the network.")
            raise e
    
    def get_all_balances(self):
        try:
            account = self.server.accounts().account_id(self.account_id).call()
            balances = account['balances']

            balance_data = []
            asset_issuers = self.config.get('asset_issuers', {})
            for asset_code, asset_issuer in asset_issuers.items():
                for balance in balances:
                    current_asset_code = "XLM" if balance['asset_type'] == 'native' else balance.get('asset_code', 'Unknown')
                    current_asset_issuer = balance.get('asset_issuer', 'Stellar Foundation')
                    if current_asset_code == asset_code and current_asset_issuer == asset_issuer:
                        balance_data.append({
                            'Asset': current_asset_code,
                            'Balance': float(balance['balance']),
                        })
            logging.info(f"Fetched balances: \n{pd.DataFrame(balance_data)}")
            self.balances = balance_data
            return balance_data
        except Exception as e:
            logging.error(f"Error fetching balances: {e}")
            return pd.DataFrame(columns=['Asset', 'Balance'])

    def get_asset_balance(self, asset_code):
        self.balances = self.get_all_balances()
        for balance in self.balances:
            if balance['Asset'] == asset_code:
                return balance['Balance']


    def place_order(self, amount, price, buy=True, base_fee=10000):
        try:
            self.account = self.server.load_account(self.account_id)
            base_issuer = self.config['asset_issuers'].get(self.base_asset_code)
            counter_issuer = self.config['asset_issuers'].get(self.counter_asset_code)
            amount=str(round(amount, 7))

            base_asset = Asset.native() if self.base_asset_code == "XLM" else Asset(self.base_asset_code, base_issuer)
            counter_asset = Asset.native() if self.counter_asset_code == "XLM" else Asset(self.counter_asset_code, counter_issuer)

            transaction = (
                TransactionBuilder(
                    source_account=self.account,
                    network_passphrase=self.network_passphrase,
                    base_fee=base_fee
                )
                .append_operation(
                    ManageBuyOffer(
                        buying=base_asset,
                        selling=counter_asset,
                        amount=amount,
                        price=str(price)
                    ) if buy else ManageSellOffer(
                        selling=base_asset,
                        buying=counter_asset,
                        amount=amount,
                        price=str(price)
                    )
                )
                .set_timeout(30)
                .build()
            )

            transaction.sign(self.keypair)
            response = self.server.submit_transaction(transaction)

            # Check if the transaction was successful
            if response['successful']:
                logging.info(f"Order placed successfully: {response}")
                return response
            else:
                logging.error(f"Order placement failed: {response}")
                return None

        except Exception as e:
            logging.error(f"Error placing order: {e}")
            return None


    def change_buy_order_price(self, 
                               offer_id: str, 
                               amount: float, 
                               new_price: float, 
                               base_fee=10000):
        try:
            offer_id = int(offer_id)  # Ensure offer_id is an integer
            amount = float(amount)  # Ensure amount is a float

            # Determine the asset types
            base_issuer = self.config['asset_issuers'].get(self.base_asset_code)
            counter_issuer = self.config['asset_issuers'].get(self.counter_asset_code)
            base_asset = Asset.native() if self.base_asset_code == "XLM" else Asset(self.base_asset_code, base_issuer)
            counter_asset = Asset.native() if self.counter_asset_code == "XLM" else Asset(self.counter_asset_code, counter_issuer)

            # Create a transaction to modify the existing order
            transaction = (
                TransactionBuilder(
                    source_account=self.account,
                    network_passphrase=self.network_passphrase,
                    base_fee=base_fee
                )
                .append_operation(
                    ManageBuyOffer(
                        buying=base_asset,
                        selling=counter_asset,
                        amount=str(round(amount, 7)),  # Limit amount to 7 decimal places
                        price=str(new_price),
                        offer_id=offer_id  # Pass the correct integer value for offer_id
                    )
                )
                .set_timeout(30)
                .build()
            )

            # Sign the transaction
            transaction.sign(self.keypair)
            
            # Submit the transaction
            response = self.server.submit_transaction(transaction)

            # Debugging: Log the entire response for inspection
            logging.debug(f"Transaction response: {response}")

            if response:
                logging.info(f"Successfully changed order price. Order {offer_id} price changed to {new_price}")
                return response
            else:
                logging.error("Failed in changing order price.")
                return None

        except Exception as e:
            logging.error(f"Error changing order price: {e}")
            return None

    def get_offer_id_from_ledger(self, ledger_num):
        offers = self.server.offers().for_account(self.account_id).call()
        for offer in offers['_embedded']['records']:
            # print('offer: ', offer)
            if offer['last_modified_ledger'] == ledger_num:
                offer_id = offer['id']
                return offer_id # Means the offer is still open
        
        return None # Means the offer was excuted
    
    def get_ledger_close_time(self, ledger_num: int) -> str:
        try:
            # Fetch details about the specific ledger
            ledger = self.server.ledgers().ledger(ledger_num).call()
            close_time = ledger.get('closed_at')
            
            if not close_time:
                raise ValueError(f"Close time not found for ledger {ledger_num}")
            
            return close_time
        except NotFoundError:
            logging.error(f"Ledger {ledger_num} not found.")
            raise ValueError(f"Ledger {ledger_num} not found.")
        except Exception as e:
            logging.error(f"Error fetching ledger {ledger_num}: {e}")
            raise ValueError(f"An error occurred while fetching ledger {ledger_num}: {e}")

    def check_offer_executed(self, offer_id: str) -> bool:
        try:
            offers = self.server.offers().for_account(self.account_id).call()
            for offer in offers['_embedded']['records']:
                if offer['id'] == offer_id:
                    return False # Means the offer is still open
            return True

        except Exception as e:
            logging.error(f"Error checking trade execution: {e}")
            return False

    ############################################################################   
    def make_exchange_order_new(self, 
                                exchange: Exchange,
                                price: float,
                                buy: bool):
        placed_order = self.place_order(amount=exchange.base_amount,
                                        price=price,
                                        buy=buy)
        # print('placed_order: ', placed_order)
        if placed_order:
            ledger_num = placed_order['ledger']
            offer_id = self.get_offer_id_from_ledger(ledger_num)
            print('placed offer_id: ', offer_id)

            if offer_id:
                exchange.buy_order.offer_id=offer_id if buy else '',
                exchange.sell_order.offer_id='' if buy else offer_id
                exchange.history_append(order_type='buy' if buy else 'sell',
                                        ledger_num=ledger_num,
                                        timestamp=placed_order['created_at'],
                                        price=price,
                                        status='open')
            elif offer_id is None:
                ledger_close_time = self.get_ledger_close_time(ledger_num=ledger_num)
                exchange.history_append(order_type='buy' if buy else 'sell',
                                        ledger_num=ledger_num,
                                        timestamp=ledger_close_time,
                                        price=price,
                                        status='executed')
            exchange.status = 'buy' if buy else 'sell'
            return exchange
        else:
            return None

    def create_new_exchange(self, 
                            base_amount: float,
                            price: float):
        exchange = Exchange(base_amount=base_amount)
        exchange = self.make_exchange_order_new(exchange=exchange,
                                                price=price,
                                                buy=True)
        if exchange:
            self.exchanges.append(exchange)


    def make_exchange_buy_order_price_changed(self, 
                                              exchange: Exchange,
                                              new_price: float):
        changed_order = self.change_buy_order_price(offer_id=exchange.buy_order.offer_id,
                                                    amount=exchange.base_amount,
                                                    new_price=new_price,)
        # print('changed_order: ', changed_order)
        if changed_order:
            ledger_num = changed_order['ledger']
            offer_id = self.get_offer_id_from_ledger(ledger_num)
            print('changed offer_id: ', offer_id)

            if offer_id: # Open
                exchange.history_append(order_type='buy',
                                        ledger_num=ledger_num,
                                        timestamp=changed_order['created_at'],
                                        price=new_price,
                                        status='open')
            elif offer_id is None: # Excuted
                ledger_close_time = self.get_ledger_close_time(ledger_num=ledger_num)
                exchange.history_append(order_type='buy',
                                        ledger_num=ledger_num,
                                        timestamp=ledger_close_time,
                                        price=new_price,
                                        status='executed')
            return exchange
        else:
            return None

    #######################################################################################
    def do_exchange(self, 
                    current_price,
                    mean_price,
                    price_std_dev):
        # price_dict = new_trade_list[0]['price']
        # current_price = float(price_dict['n']) / float(price_dict['d'])
        one_percent_price = price_std_dev * 2 / 100
        counter_asset_balance = self.get_asset_balance(self.counter_asset_code)
        counter_amount = counter_asset_balance * self.trading_capital_percent / 100
        
        try:
            if len(self.exchanges) < 1:  # First exchange -- place a buy order
                buy_price = current_price - self.price_interval_percent*one_percent_price
                buy_price = round(buy_price, 7)
                base_amount = counter_amount / buy_price

                self.create_new_exchange(base_amount=base_amount,
                                         price=buy_price)
                
            else:
                for exchange in self.exchanges:
                    # print('exchange.buy_offer_id:', exchange.buy_offer_id)
                    # print('exchange.buy_offer_id:', exchange.buy_offer_id)
                    if exchange.status == "buy":  # buy status
                        if exchange.buy_order.history[-1]['status'] == 'open':
                            if self.check_offer_executed(exchange.buy_order.offer_id):  # If the buy order was executed
                                last_history = exchange.buy_order.history[-1]
                                ledger_num = last_history['ledger_num']
                                ledger_close_time = self.get_ledger_close_time(ledger_num)
                                buy_price = last_history['price']
                                exchange.history_append(order_type='buy',
                                                        ledger_num=ledger_num,
                                                        timestamp=ledger_close_time,
                                                        price=buy_price,
                                                        status='executed')
                                
                            else:  # Buy order not executed yet, modify the price if necessary
                                if abs(current_price - exchange.buy_order.history[-1]['price']) > self.price_interval_percent * one_percent_price:
                                    new_buy_price = current_price - self.price_interval_percent * one_percent_price
                                    new_buy_price = round(new_buy_price, 7)
                                    self.make_exchange_buy_order_price_changed(exchange=exchange,
                                                                            new_price=new_buy_price)
                        elif exchange.buy_order.history[-1]['status'] == 'executed':
                                last_history = exchange.buy_order.history[-1]
                                buy_price = last_history['price']

                                # Place the sell order
                                sell_price = max(buy_price, current_price) + self.price_interval_percent * one_percent_price
                                sell_price = round(sell_price, 7)
                                self.make_exchange_order_new(exchange=exchange,
                                                            price=sell_price,
                                                            buy=False)
                                
                                # Place a new exchange and buy order
                                new_buy_price = min(buy_price, current_price) - self.price_interval_percent * one_percent_price
                                new_buy_price = round(new_buy_price, 7)
                                base_amount = counter_amount / new_buy_price
                                self.create_new_exchange(base_amount=base_amount,
                                                         price=new_buy_price)
                        else:
                            raise ValueError(f"exchange.buy_order.history[-1]['status'] is not 'open' or 'executed'. ")
                                
                    elif exchange.status == "sell": # Sell order placed last
                        if exchange.sell_order.history[-1]['status'] == 'open':
                            if self.check_offer_executed(exchange.sell_order.offer_id):  # If the sell order was executed
                                last_history = exchange.sell_order.history[-1]
                                ledger_num = last_history['ledger_num']
                                ledger_close_time = self.get_ledger_close_time(ledger_num)
                                price = last_history['price']
                                exchange.history_append(order_type='sell',
                                                        ledger_num=ledger_num,
                                                        timestamp=ledger_close_time,
                                                        price=price,
                                                        status='executed')
                                
                                # Now place a new exchange-buy order below the sell price
                                new_buy_price = sell_price - self.price_interval_percent * one_percent_price
                                base_amount = counter_amount / new_buy_price

                                self.create_new_exchange(base_amount=base_amount,
                                                         price=new_buy_price)
                            else:
                                pass
                        elif exchange.sell_order.history[-1]['status'] == 'executed':
                            pass
                        else:
                            raise ValueError(f"exchange.sell_order.history[-1]['status'] is not 'open' or 'executed'. ")
                    else:
                            raise ValueError(f"exchange.status is not 'buy' or 'sell'. ")
        except Exception as e:
            logging.error(f"Error in do_exchange: {e}")





    def fetch_trading_history(self):
        try:
            transactions = self.server.transactions().for_account(self.keypair.public_key).limit(200).order(desc=True).call()
            trades = []

            for transaction in transactions['_embedded']['records']:
                operations = self.server.operations().for_transaction(transaction['id']).call()['_embedded']['records']
                
                for operation in operations:
                    if operation['type'] in ['manage_buy_offer', 'manage_sell_offer']:
                        action = "Buy" if operation['type'] == 'manage_buy_offer' else "Sell"
                        buy_asset = operation.get('buying_asset_code', 'XLM')
                        sell_asset = operation.get('selling_asset_code', 'XLM')
                        amount = float(operation.get('amount', 0))
                        price = float(operation.get('price', 0))
                        total = amount * price

                        trades.append({
                            "Time": transaction['created_at'],
                            "Sell": sell_asset,
                            "Buy": buy_asset,
                            "Amount": amount,
                            "Price": price,
                            "Total": total
                        })

            trades_df = pd.DataFrame(trades) if trades else pd.DataFrame(columns=["Time", "Sell", "Buy", "Amount", "Price", "Total"])
            logging.info(f"Fetched trades: {trades_df}")
            return trades_df

        except Exception as e:
            logging.error(f"Error fetching trading history: {e}")
            return pd.DataFrame(columns=["Time", "Sell", "Buy", "Amount", "Price", "Total"])


    