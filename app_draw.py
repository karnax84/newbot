import logging
import pandas as pd
import streamlit as st

from utils.time_conversions import convert_time_to_display

# Set up logging configuration
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO  # Set the log level (can be changed to DEBUG for more details)
)

# %%
def write_asset_balance(asset_code: str = "VELO"):
    if st.session_state['balances']:
        for balance in st.session_state['balances']:
            if balance['Asset'] == asset_code:
                # logging.info(f"Displaying available balance: {balance['Balance']} {asset_code}")
                st.write(f"Available: {balance['Balance']} {asset_code}")
    else:
        st.write(f"Available: 0 {asset_code}")


def account_balance_table():
    st.write("**Account Balances**")
    st.dataframe(pd.DataFrame(st.session_state['balances']), 
                height=140, 
                use_container_width=True,
                hide_index=True)
    
def trading_actions_table():
    st.write("**Trading Actions**")
    trading_actions_data = []
    for exchange in st.session_state['exchanges_list']:
        base_asset_code = st.session_state["base_asset_code"]
        base_amount = exchange.base_amount

        buy_price = round(exchange.buy_order.history[-1]['price'], 7)
        buy_status = exchange.buy_order.history[-1]['status']
        buy_timestamp = exchange.buy_order.history[-1]['timestamp']
        status = 'Buying' if exchange.buy_order.history[-1]['status'] == 'open' else 'Bought'

        if len(exchange.sell_order.history) > 0:
            sell_price = round(exchange.sell_order.history[-1]['price'], 7)
            sell_status = exchange.sell_order.history[-1]['status']
            sell_timestamp = exchange.sell_order.history[-1]['timestamp']
            status = 'Selling' if exchange.sell_order.history[-1]['status'] == 'open' else 'Done'

        trading_actions_data.append({
            'Asset': base_asset_code,
            'Amount': base_amount,
            'Buy': str(buy_price),
            'Sell': str(sell_price) if len(exchange.sell_order.history) > 0 else '',
            'Status': status
        })

    st.dataframe(pd.DataFrame(trading_actions_data), 
                height=490, 
                use_container_width=True,
                hide_index=True)

# %%
import plotly.graph_objects as go

def draw_chart():
    if not st.session_state['trade_df'].empty:
        # Extract timestamps and prices, and calculate range
        timestamps = st.session_state['trade_df']['timestamp']
        prices = st.session_state['trade_df']['price']
        x_min = timestamps.min()
        x_max = timestamps.max()
        x_range = x_max - x_min
        extra_space = x_range / 4  # Calculate 1/4th of the x-axis range

        # Calculate ymin and ymax
        ymin = prices.min()
        ymax = prices.max()
        
        # Calculate padding (1/8th of the y-axis range)
        y_range = ymax - ymin
        y_padding = y_range / 8

        # Adjust ymin and ymax for padding
        adjusted_ymin = ymin - y_padding
        adjusted_ymax = ymax + y_padding

        # Define chart layout adjustments
        chart_layout_adjustments = {
            "margin": dict(l=20, r=20, t=20, b=20),
            "xaxis": {
                "title": "Time (UTC-0)",
                "automargin": True,
                "range": [x_min, x_max + extra_space],
                "rangeslider": {"visible": False}
            },
            "yaxis": {
                "title": f"{st.session_state['base_asset_code']}/{st.session_state['counter_asset_code']}",
                "automargin": True,
                "range": [adjusted_ymin, adjusted_ymax]  # Adjusted y-axis range with padding
            },
            "yaxis2": {
                "title": "Volume",
                "overlaying": "y",
                "side": "right"
            },
            "height": 500,
            "showlegend": False
        }
    
        # Create figure and add traces
        fig_line = go.Figure()

        # Add price line trace
        fig_line.add_trace(go.Scatter(
            x=st.session_state['trade_df']['timestamp'],
            y=st.session_state['trade_df']['price'],
            mode='lines',
            line_shape="hv",
            name='Price'
        ))

        # Add volume bar trace
        fig_line.add_trace(go.Bar(
            x=st.session_state['trade_df']['timestamp'],
            y=st.session_state['trade_df']['volume'],
            name='Volume',
            yaxis='y2',
            opacity=0.3
        ))

        # Add horizontal dotted line at the mean price
        mean_price = st.session_state["mean_price"]
        fig_line.add_trace(go.Scatter(
            x=[x_min, x_max],
            y=[mean_price, mean_price],
            mode='lines',
            line=dict(width=1, dash='dot', color='green'),
            name='Mean Price'
        ))
        fig_line.add_trace(go.Scatter(
            x=[x_min],
            y=[mean_price],
            mode='text',
            text=[f"Mean: {mean_price:.8f}"],
            textposition='top right',
            textfont=dict(size=12, color='green')
        ))
        
        # Add horizontal dotted line at the upper and lower std_dev prices
        upper_std_dev_price = st.session_state["mean_price"] + st.session_state["price_std_dev"]
        lower_std_dev_price = st.session_state["mean_price"] - st.session_state["price_std_dev"]
        fig_line.add_trace(go.Scatter(
            x=[x_min, x_max],
            y=[upper_std_dev_price, upper_std_dev_price],
            mode='lines',
            line=dict(width=1, dash='dot', color='red'),
            name='Upper Standard Deviation Price'
        ))
        fig_line.add_trace(go.Scatter(
            x=[x_min],
            y=[upper_std_dev_price],
            mode='text',
            text=[f"Upper Standard Deviation: {upper_std_dev_price:.8f}"],
            textposition='top right',
            textfont=dict(size=12, color='red')
        ))
        
        fig_line.add_trace(go.Scatter(
            x=[x_min, x_max],
            y=[lower_std_dev_price, lower_std_dev_price],
            mode='lines',
            line=dict(width=1, dash='dot', color='red'),
            name='Lower Standard Deviation Price'
        ))
        fig_line.add_trace(go.Scatter(
            x=[x_min],
            y=[lower_std_dev_price],
            mode='text',
            text=[f"Lower Standard Deviation: {lower_std_dev_price:.8f}"],
            textposition='top right',
            textfont=dict(size=12, color='red')
        ))
        
        # # Add horizontal dotted line at the buy and sell limit price
        # sell_limit_price = st.session_state["mean_price"] + st.session_state["price_std_dev"]/2
        # buy_limit_price = st.session_state["mean_price"] - st.session_state["price_std_dev"]/2
        # fig_line.add_trace(go.Scatter(x=[x_max, x_max + extra_space],
        #                               y=[sell_limit_price, sell_limit_price],
        #                               mode='lines',
        #                               line=dict(width=1, dash='dot', color='magenta'),
        #                               name='Sell Limit Price'))
        # fig_line.add_trace(go.Scatter(x=[x_max + extra_space],
        #                               y=[sell_limit_price],
        #                               mode='text',
        #                               text=[f"Sell Limit"],
        #                               textposition='top left',
        #                               textfont=dict(size=12, color='magenta')))
        
        # fig_line.add_trace(go.Scatter(x=[x_max, x_max + extra_space],
        #                               y=[buy_limit_price, buy_limit_price],
        #                               mode='lines',
        #                               line=dict(width=1, dash='dot', color='magenta'),
        #                               name='Sell Limit Price'))
        # fig_line.add_trace(go.Scatter(x=[x_max + extra_space],
        #                               y=[buy_limit_price],
        #                               mode='text',
        #                               text=[f"Buy Limit"],
        #                               textposition='top left',
        #                               textfont=dict(size=12, color='magenta')))
        
        # Add horizontal dotted line at the current price
        current_price = st.session_state["current_price"]
        fig_line.add_trace(go.Scatter(
            x=[x_max, x_max + extra_space],
            y=[current_price, current_price],
            mode='lines',
            line=dict(width=1, dash='dot', color='blue'),
            name='Current Price'
        ))
        fig_line.add_trace(go.Scatter(
            x=[x_max],
            y=[current_price],
            mode='text',
            text=[f"Current: {current_price:.8f}"],
            textposition='top right',
            textfont=dict(size=12, color='blue')
        ))
        
        # Add vertical dotted line at the last trade time
        last_trade_timestamp = st.session_state["last_trade_time"]
        fig_line.add_trace(go.Scatter(
            x=[last_trade_timestamp, last_trade_timestamp],
            y=[adjusted_ymin, adjusted_ymax],
            mode='lines',
            line=dict(width=1, dash='dot', color='blue'),
            name='Last Trade Time'
        ))
        fig_line.add_trace(go.Scatter(
            x=[last_trade_timestamp],
            y=[adjusted_ymin],
            mode='text',
            text=[f"Last Trade: {convert_time_to_display(last_trade_timestamp)}"],
            textposition='top right',
            textfont=dict(size=12, color='blue')
        ))

        # Add vertical dotted line at the last update time
        last_update_timestamp = st.session_state["last_update_time"]
        fig_line.add_trace(go.Scatter(
            x=[last_update_timestamp, last_update_timestamp],
            y=[ymin, ymax],
            mode='lines',
            line=dict(width=1, dash='dot', color='green'),
            name='Last Trade Time'
        ))
        fig_line.add_trace(go.Scatter(
            x=[last_update_timestamp],
            y=[ymin],
            mode='text',
            text=[f"Last Update: {convert_time_to_display(last_update_timestamp)}"],
            textposition='top right',
            textfont=dict(size=12, color='green')
        ))

        ### Plot historical buy/sell signals ###
        # Overlay Buy/Sell signals from the exchange history
        for exchange in st.session_state['exchanges_list']:
            
            # Buy signals
            buy_signals = []
            executed_buy_signals = []
            
            for entry in exchange.buy_order.history:
                timestamp = entry['timestamp']
                price = entry['price']
                buy_signals.append((timestamp, price))
                
                # Check if the order is executed and mark it
                if entry['status'] == 'executed':
                    executed_buy_signals.append((timestamp, price))
            
            last_entry = exchange.buy_order.history[-1]
            if last_entry['status'] != 'executed':
                buy_signals.append((last_update_timestamp, last_entry['price']))
            
            # Plot buy signals (green line)
            if buy_signals:
                buy_timestamps, buy_prices = zip(*buy_signals)
                fig_line.add_trace(go.Scatter(
                    x=buy_timestamps,
                    y=buy_prices,
                    mode='lines',
                    line_shape="hv",
                    line=dict(color='green', width=2),
                    name='Buy'
                ))
            
            # Plot executed buy signals (green markers)
            if executed_buy_signals:
                executed_buy_timestamps, executed_buy_prices = zip(*executed_buy_signals)
                fig_line.add_trace(go.Scatter(
                    x=executed_buy_timestamps,
                    y=executed_buy_prices,
                    mode='markers',
                    marker=dict(color='green', size=10, symbol='circle'),
                    name='Executed Buy'
                ))

            if len(exchange.sell_order.history) > 0:
                # Sell signals
                sell_signals = []
                executed_sell_signals = []
                
                for entry in exchange.sell_order.history:
                    timestamp = entry['timestamp']
                    price = entry['price']
                    sell_signals.append((timestamp, price))
                    
                    # Check if the order is executed and mark it
                    if entry['status'] == 'executed':
                        executed_sell_signals.append((timestamp, price))
                
                last_entry = exchange.sell_order.history[-1]
                if last_entry['status'] != 'executed':
                    sell_signals.append((last_update_timestamp, last_entry['price']))
                
                # Plot sell signals (red line)
                if sell_signals:
                    sell_timestamps, sell_prices = zip(*sell_signals)
                    fig_line.add_trace(go.Scatter(
                        x=sell_timestamps,
                        y=sell_prices,
                        mode='lines',
                        line_shape="hv",
                        line=dict(color='red', width=2),
                        name='Sell'
                    ))

                # Plot executed sell signals (red markers)
                if executed_sell_signals:
                    executed_sell_timestamps, executed_sell_prices = zip(*executed_sell_signals)
                    fig_line.add_trace(go.Scatter(
                        x=executed_sell_timestamps,
                        y=executed_sell_prices,
                        mode='markers',
                        marker=dict(color='red', size=10, symbol='x'),
                        name='Executed Sell'
                    ))

             
        # Update layout with adjustments
        fig_line.update_layout(**chart_layout_adjustments)
        st.plotly_chart(fig_line, use_container_width=True)

    else:
        # Create empty figure with adjusted layout
        fig_line = go.Figure()
        # Define chart layout adjustments
        chart_layout_adjustments = {
            "margin": dict(l=20, r=20, t=20, b=20),
            "xaxis": {
                "title": "Time",
                "automargin": True,
                "rangeslider": {"visible": False}
            },
            "yaxis": {
                "title": f"{st.session_state['base_asset_code']}/{st.session_state['counter_asset_code']}",
                "automargin": True,
            },
            "yaxis2": {
                "title": "Volume",
                "overlaying": "y",
                "side": "right"
            },
            "height": 500,
            "showlegend": False
        }
        fig_line.update_layout(**chart_layout_adjustments)
        st.plotly_chart(fig_line, use_container_width=True)

