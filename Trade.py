import codecs
import hmac
import hashlib
import json
import requests
import sqlite3
import json
import collections
import subprocess
import sys
import time
from datetime import datetime
from pushover import init, Client

# Defines a trade class
# cc - Ticker for the cryptocurrency you are buying
# fiat - What you're using to buy the cryptocurrency
# fundsToSpend - Amount of funds to spend each time this script runs
# market - The market on Bittrex e.g DCR-USD
# purchaseFrequencyDays - Number of days to wait before another purchase
# Includes all methods necessary to submit a trade.


class trade:
    def __init__(self, cc, fiat, fundsToSpend, BittrexKey, BittrexSecret,
                 PushoverToken=None, PushoverUserKey=None, testMode=True):
        self.cc = cc
        self.fiat = fiat
        self.market = cc + '-' + fiat
        self.fundsToSpend = fundsToSpend
        self.BittrexKey = BittrexKey
        self.BittrexSecret = BittrexSecret
        self.PushoverToken = PushoverToken
        self.PushoverUserKey = PushoverUserKey
        self.testMode = testMode
        self.askPrice = self.GetAskPrice()
        init(PushoverToken)

    def GetAskPrice(self):
        jsonStr = self.getMarket(self.market)
        return float(jsonStr['askRate'])

    def Submit(self):
        self.buyCryptocurrency(
            self.cc, self.market, self.fundsToSpend, self.askPrice, self.testMode)

    def signMessage(self, message):
        "Function to sign an API call"
        signature = hmac.new(codecs.encode(self.BittrexSecret),
                             codecs.encode(message), hashlib.sha512).hexdigest()
        return signature

    def generateHash(self, message):
        "Function to generate a hash of a message"
        hash = hashlib.sha512(str(message).encode("utf-8")).hexdigest()
        return hash

    def now_milliseconds(self):
        "Function to return timestamp in milliseconds"
        return int(time.time() * 1000)

    ######################################################################
    # Bittrex API v3

    def getMarket(self, market):
        "GET /markets/{marketSymbol}/ticker"
        timestamp = str(self.now_milliseconds())
        uri = 'https://api.bittrex.com/v3/markets/' + market + '/ticker'
        method = "GET"
        contentHash = self.generateHash("")
        subaccountId = ""
        preSign = timestamp + uri + method + contentHash + subaccountId
        signature = self.signMessage(preSign)
        headers = {
            'content-type': 'application/json',
            'Api-Key': self.BittrexKey,
            'Api-Timestamp': timestamp,
            'Api-Content-Hash': contentHash,
            'Api-Signature': signature
        }
        response = requests.get(uri, headers=headers)
        # print(response.text)
        jsonStr = json.loads(response.text)
        return jsonStr

    def postOrder(self, market, direction, type, timeInForce, quantity):
        "POST /orders"
        timestamp = str(self.now_milliseconds())
        uri = ('https://api.bittrex.com/v3/orders')
        method = "POST"
        orderRequest = {
            "marketSymbol": market,
            "direction": direction,
            "type": type,
            "quantity": quantity,
            "timeInForce": timeInForce
        }
        orderRequestJson = json.dumps(orderRequest)
        contentHash = self.generateHash(orderRequestJson)
        subaccountId = ""
        preSign = timestamp + uri + method + contentHash + subaccountId
        signature = self.signMessage(preSign)

        headers = {
            'content-type': 'application/json',
            'Api-Key': self.BittrexKey,
            'Api-Timestamp': timestamp,
            'Api-Content-Hash': contentHash,
            'Api-Signature': signature
        }

        response = requests.post(uri, data=orderRequestJson, headers=headers)
        print(response.text)
        jsonStr = json.loads(response.text)
        return jsonStr

    def getAvailableHoldings(self, ticker):
        "GET /balances/{currencySymbol}"
        timestamp = str(self.now_milliseconds())
        uri = 'https://api.bittrex.com/v3/balances/' + ticker
        method = "GET"
        contentHash = self.generateHash("")
        subaccountId = ""
        preSign = timestamp + uri + method + contentHash + subaccountId
        signature = self.signMessage(preSign)
        headers = {
            'content-type': 'application/json',
            'Api-Key': self.BittrexKey,
            'Api-Timestamp': timestamp,
            'Api-Content-Hash': contentHash,
            'Api-Signature': signature
        }

        response = requests.get(uri, headers=headers)
        # print(response.text)
        jsonStr = json.loads(response.text)
        availableFunds = jsonStr["available"]
        return availableFunds

    ######################################################################
    # Methods to take advantage of Bittrex API methods

    def buyCryptocurrency(self, cc, market, orderAmount, askPrice, testMode):
        "Generate market buy at asking price"
        quantity = orderAmount / askPrice
        quantity = round(quantity, 8)
        total = round(quantity * askPrice, 8)
        print('Buying ' + str(quantity) + ' ' + str(cc) + ' for a total of $'
              + str(round(total, 2)) + ' at $' + str(round(askPrice, 2)) + ' each.')

        if (testMode != True):
            response = self.postOrder(market, 'BUY', 'MARKET',
                                      'IMMEDIATE_OR_CANCEL', quantity)
            if response.get("id"):
                self.saveTrade('Bought', cc, quantity, askPrice, total)
                self.PushoverNotify('Bought ' + str(quantity) + str(cc)
                                    + ' for $' + str(round(total, 2)), cc + ' Purchase')
            else:
                self.PushoverNotify('Buy order failed. Reason: ' + str(response),
                                    cc + ' Purchase Failed')
                print('Buy order failed. Reason: ' + response["code"])
        else:
            print('**TEST MODE**')
            self.saveTrade('Bought', cc, quantity, askPrice, total, testMode)
            self.PushoverNotify('**TEST MODE**: Bought ' + str(quantity) + str(cc)
                                + ' for $' + str(round(total, 2)), cc + ' Purchase')

    def PushoverNotify(self, message, title):
        if (self.PushoverToken):
            Client(self.PushoverUserKey).send_message(message, title=title)

    def saveTrade(self, action, cc, quantity, price, total, testMode=False):
        "Save trade details to a file called 'lasttrade.txt'"
        trade = {
            'action': action,
            'cryptocurrency': cc,
            'quantity': quantity,
            'price': price,
            'totalPrice': total,
            'tradeTime': str(datetime.now()),
            'testMode': testMode
        }

        with open('tradehistory.txt', 'a+') as outfile:
            # try:
            #   existingHistory = outfile.readlines()
            #   updatedHistory = existingHistory + '\n' + str(trade)
            #   print(updatedHistory, file=outfile)
            # except:
          print(str(trade), file=outfile)
