class Order:
    def __init__(self,
                #  base_asset_code: str, 
                #  counter_asset_code: str, 
                 order_type: str, # 'buy' / 'sell'
                 base_amount: float,
                 offer_id: str = "", 
                 ):
        # self.base_asset_code = base_asset_code
        # self.counter_asset_code = counter_asset_code
        self.order_type = order_type
        self.base_amount = base_amount
        self.offer_id = offer_id

        self.history: list[dict] = []

    def history_append(self, 
                       ledger_num: int, 
                       timestamp: str, 
                       price: float, 
                       status: str): # 'open' / 'executed'
        self.history.append({'ledger_num': ledger_num,
                             'timestamp': timestamp,
                             'price': price,
                             'status': status})

class Exchange:
    def __init__(self, 
                #  base_asset_code: str, 
                #  counter_asset_code: str, 
                 base_amount: float, 
                 buy_offer_id: str='', 
                 sell_offer_id: str='') -> None:
        # self.base_asset_code = base_asset_code
        # self.counter_asset_code = counter_asset_code
        self.base_amount = base_amount

        self.buy_order = Order(order_type='buy',
                               base_amount=base_amount,
                               offer_id=buy_offer_id)

        self.sell_order = Order(order_type='sell',
                                base_amount=base_amount,
                                offer_id=sell_offer_id)
        self.status: str = ''
    def history_append(self, 
                       order_type: str, 
                       ledger_num: int,
                       timestamp: str, 
                       price: float, 
                       status: str):
        if order_type == 'buy':
            self.buy_order.history_append(ledger_num=ledger_num,
                                          timestamp=timestamp,
                                          price=price,
                                          status=status)
        if order_type == 'sell':
            self.sell_order.history_append(ledger_num=ledger_num,
                                           timestamp=timestamp,
                                           price=price,
                                           status=status)