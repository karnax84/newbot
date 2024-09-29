# Stellar Dynamic Algorithmic Trading System

## Stellar Network and Stellar Trading

### Stellar Network

The **Stellar Network** is a pioneering blockchain platform that facilitates efficient and cost-effective cross-border transactions between different currencies and financial systems. Established in 2014 by Jed McCaleb and Joyce Kim, Stellar's goal is to bridge the gap between financial institutions, payment systems, and individuals, providing a decentralized and accessible platform for global payments.

**Key Features of the Stellar Network:**

- **Decentralization:** Operates on a decentralized ledger, removing intermediaries and enhancing transparency and security in transactions.
- **Stellar Consensus Protocol (SCP):** Utilizes SCP to achieve rapid and reliable transaction confirmation, differing from traditional consensus mechanisms like proof-of-work or proof-of-stake.
- **Low Transaction Fees:** Designed to minimize transaction costs, making it suitable for both high-frequency trading and microtransactions, thereby fostering financial inclusion.
- **Rapid Transaction Processing:** Processes transactions in seconds, enabling near-instantaneous settlement and significantly improving operational efficiency.

### Stellar Trading
https://stellarterm.com/

https://stellarterm.com/markets/top/

**Stellar Trading** encompasses the buying and selling of cryptocurrencies and digital assets on the Stellar network. By leveraging the capabilities of Stellar’s blockchain, traders can engage in efficient, low-cost trading of various cryptocurrency pairs.

**Key Aspects of Stellar Trading:**

- **Trading Platforms:** Platforms such as StellarTerm offer intuitive interfaces for trading on Stellar’s decentralized exchange, providing access to real-time market data, order books, and trading functionalities.
- **Cryptocurrency Pairs:** Stellar trading typically involves pairs like XLM (Stellar’s native asset) and other digital assets, allowing traders to implement diverse strategies for market optimization.
- **Order Types:** Traders can use limit orders to buy or sell at specific prices or market orders to execute trades at the prevailing market price. This flexibility supports various trading strategies, including algorithmic and manual trading approaches.
- **Decentralized Exchange:** The decentralized nature of Stellar’s exchange model facilitates direct trades between users, enhancing security, transparency, and efficiency.

With its innovative features and robust trading capabilities, the Stellar Network provides a powerful platform for executing and optimizing cryptocurrency trades. By leveraging Stellar’s rapid transaction processing, low fees, and decentralized structure, traders can implement effective and cost-efficient trading strategies on a global scale.

## Trading Cryptocurrency Pairs

The trading program will written for only two crypto trading pairs: 

1. VELO / XLM,  
2. SHX / XLM.  

No other cryptocurrencies will be used.

## Trading Amount

All trades will utilize 1% of trading capital.

## Dynamic Limit Order Strategy

### Strategy Overview

The **Dynamic Limit Order Strategy** is designed to adapt to market fluctuations by continuously adjusting buy orders based on price movements. This strategy aims to capitalize on market trends and maintain an active trading position.

**Steps:**

1. **Price Conversion:**
   - Convert the current price into a percentage scale, where 0% represents the lowest historical price and 100% represents the current price. Prices above the current price are represented as 101% and higher.

2. **Initial Buy Order:**
   - Place a LIMIT BUY ORDER 1% below the current price.

3. **Trade Execution:**
   - **If the price decreases and triggers the buy order:**
     - Place a LIMIT SELL ORDER 1% above the executed buy order to close the trade.
     - Place a new LIMIT BUY ORDER 1% below the previous buy order.

   - **If the price increases and triggers the sell order (closing the trade):**
     - Place a new LIMIT BUY ORDER 1% below the price at which the sell order was executed.

4. **Ongoing Buy Order Management:**
   - Maintain an open LIMIT BUY ORDER at a price less than 5% below the current price.
   - If the current price exceeds 5% above the last LIMIT BUY ORDER:
     - Open new LIMIT BUY ORDERS at 1% intervals above the previous LIMIT BUY ORDER until the current price is less than 5% above the closest BUY LIMIT ORDER.

This strategy ensures continuous adaptation to market conditions, allowing traders to remain active and capitalize on price movements.

### LIMIT BUY ORDER and LIMIT SELL ORDER

- **LIMIT BUY ORDER:** An order to purchase an asset at a specified price or lower. The order is executed only if the asset’s price reaches or falls below the set limit price.
    - **Purpose:** To ensure purchasing at or below a desired price.
    - **Example:** A LIMIT BUY ORDER for Bitcoin at $20,000 will be executed only if Bitcoin’s price drops to $20,000 or lower.

- **LIMIT SELL ORDER:** An order to sell an asset at a specified price or higher. The order is executed only if the asset’s price reaches or exceeds the set limit price.
    - **Purpose:** To ensure selling at or above a desired price.
    - **Example:** A LIMIT SELL ORDER for Bitcoin at $25,000 will be executed only if Bitcoin’s price rises to $25,000 or higher.

**Key Points:**
- **Limit Buy Orders** enable purchasing assets at a price lower than the current market price.
- **Limit Sell Orders** facilitate selling assets at a price higher than the current market price.

These orders provide traders with precise control over their entry and exit points, optimizing trade execution and strategy effectiveness.

