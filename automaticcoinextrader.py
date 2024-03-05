$pip install ta
$pip install ccxt


import sys
import pandas as pd
import ta
import time
import requests
import json
from datetime import datetime
from math import floor, log10
import ccxt


# CoinEx exchange
exchange = ccxt.coinex()


########################
### Authentification ###
########################

authentication = {
        "apiKey": "",
        "secret": "",
}





############
### Data ###
############
symbol_base = ""
symbol_quote = "USDT"
timeframe = "1day"


url='https://api.kucoin.com'
go_back = 2*365
starting_date = float(round(time.time()))-go_back*24*3600


check = True
while check:
    data = requests.get(url + f'/api/v1/market/candles?type={timeframe}&symbol={symbol_base}-{symbol_quote}&startAt={int(starting_date)}')
    data = data.json()
    check = 'msg' in data.keys()


data = pd.DataFrame(data['data'], columns = ['timestamp', 'open', 'close', 'high', 'low', 'amount', 'volume'])
data["close"] = pd.to_numeric(data["close"])
data['timestamp'] = pd.to_datetime(data['timestamp'], unit='s')
data = data.iloc[::-1]



################
### Strategy ###
################
data['EMA-st'] = ta.trend.ema_indicator(data['close'], 12)
data['EMA-lt'] = ta.trend.ema_indicator(data['close'], 18)
data['RSI'] = ta.momentum.rsi(data['close'])
data = data.iloc[-2]


entry = data['EMA-st'] > data['EMA-lt'] and data['RSI'] < 70
take_profit = data['EMA-st'] < data['EMA-lt'] and data['RSI'] > 30



############
### Prep ###
############
### Balances
exchange = ccxt.coinex(authentication)

# USDT
balance_quote = float(exchange.fetchBalance()[symbol_quote]['free'])
# BNB
balance_base = float(exchange.fetchBalance()[symbol_base]['free'])



### Price

symbol = (f"{symbol_base}/{symbol_quote}")

price = float(exchange.fetchTicker(symbol)['last'])




### Minimum requirements
info = requests.get(url + f'/api/v1/symbols/{symbol_base}-{symbol_quote}')
info = info.json()['data']


# Truncation
min_truncate = int(abs(log10(float(info['baseIncrement']))))
def truncate(n):
    r = floor(float(n)*10**min_truncate)/10**min_truncate
    return str(r)



############
# Min amounts
min_quote_for_buy = float(info['minFunds'])
min_base_for_sell = float(truncate(float(min_quote_for_buy)/price))

##############
### Orders ###
##############

now = datetime.now()
current_time = now.strftime("%d/%m/%Y %H:%M:%S")



if entry and balance_quote > min_quote_for_buy:
        amount = truncate(balance_quote/price)
        order_type = 'market'
        side = 'buy'
        base_price = price
        order = exchange.createOrder(symbol, order_type, side, amount, base_price)



        print(f"{current_time}: bought {amount} {symbol_base} at {price}")
        print(f"Order Details: {order}")

elif take_profit and balance_base > min_base_for_sell:
        amount = truncate(balance_base)

        order_type = 'market'
        side = 'sell'
        base_price = price
        order = exchange.createOrder(symbol, order_type, side, amount, base_price)

        print(f"{current_time}: sold {amount} {symbol_base} at {price}")
        print(f"Order Details: {order}")


else:
        print(f"Patience is virtue")
