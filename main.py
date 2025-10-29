from AlgorithmImports import *
import joblib
import numpy
import random

class TopCryptoStrategy(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2022, 1, 1) #2022
        self.SetEndDate(2024, 11, 1)
        self.set_brokerage_model(BrokerageName.BINANCE)

        self.initial_cash = 1000000
        self.SetCash(self.initial_cash)
        self.resolution = Resolution.HOUR
        self.fixed_invest = 0.9
        self.profit_margin = 0.05
        self.safety_margin = 0.05

        self.cooldown = timedelta(hours=12)
        self.prev_time = datetime(2022, 1, 1)

        #crypto_tags = ["BTCUSD", "ETHUSD", "BNBUSD", "SOLUSD", "LINKUSD", "AVAXUSD"]
        crypto_tags = ["BTCUSDT"]

        #model key = tags
        self.models = {}
        for model_key in crypto_tags:
            if self.object_store.contains_key(model_key):
                self.debug(f"Found model: {model_key}")
                file_name = self.object_store.get_file_path(model_key)
                self.models[model_key] = joblib.load(file_name)

        toggle_indicators = {
            "macd": True,
            "vwap": True,
            "rsi": True,
            "adx": True,
            "cci": True,
            "stoch": True,
            "hma": False,
            "cmo": True,
            "uo": True
        }

        self.cryptos = []
        self.indicators = {}
        self.past_indicators = {}
        self.past_signals = {}
        self.boughtPrices = {}
        self.symbol_to_tag = {}
        for crypto in crypto_tags:
            #Some initializing stuff
            symbol = self.add_crypto(crypto, self.resolution, market=Market.BINANCE).symbol
            self.cryptos.append(symbol)
            self.symbol_to_tag[symbol] = crypto

            #past data initializing
            self.boughtPrices[symbol] = 0
            self.indicators[symbol] = {}
            self.past_signals_win = 1
            self.past_signals[symbol] = RollingWindow[float](self.past_signals_win)
            self.past_indicators_win = 5
            self.past_indicators[symbol] = {}

            #Indicators::
            #constants
            self.macd_fast = 8
            self.macd_slow = 12
            self.macd_signal = 6
            self.vwap_period = 16
            self.rsi_period = 16
            self.adx_period = 16
            self.cci_period = 24
            self.sto_short = 12
            self.sto_smooth = 6
            self.hma_period = 16
            self.cmo_period = 12
            self.uo_short = 6
            self.uo_mid = 12
            self.uo_long = 18

            #MACD
            if toggle_indicators["macd"]:
                self.indicators[symbol]["macd"] = self.macd(symbol, 
                                                    self.macd_fast, 
                                                    self.macd_slow, 
                                                    self.macd_signal, 
                                                    MovingAverageType.Exponential,
                                                    self.resolution)
                
                self.past_indicators[symbol]["macd"] = RollingWindow[float](self.past_indicators_win)
            #VWAP
            if toggle_indicators["vwap"]:
                self.indicators[symbol]["vwap"] = self.vwap(symbol, self.vwap_period, self.resolution)
                self.past_indicators[symbol]["vwap"] = RollingWindow[float](self.past_indicators_win)
            #RSI
            if toggle_indicators["rsi"]:
                self.indicators[symbol]["rsi"] = self.rsi(symbol, self.rsi_period, self.resolution)
                self.past_indicators[symbol]["rsi"] = RollingWindow[float](self.past_indicators_win)
            #ADX
            if toggle_indicators["adx"]:
                self.indicators[symbol]["adx"] = self.adx(symbol, self.adx_period, self.resolution)
                self.past_indicators[symbol]["adx"] = RollingWindow[float](self.past_indicators_win)
            #CCI
            if toggle_indicators["cci"]:
                self.indicators[symbol]["cci"] = self.cci(symbol, self.cci_period, self.resolution)
                self.past_indicators[symbol]["cci"] = RollingWindow[float](self.past_indicators_win)
            #STOCH
            if toggle_indicators["stoch"]:
                self.indicators[symbol]["stoch"] = self.sto(symbol, 
                                                            self.sto_short,
                                                            self.sto_short,
                                                            self.sto_smooth)
                self.past_indicators[symbol]["stoch"] = RollingWindow[float](self.past_indicators_win)
            #HMA
            if toggle_indicators["hma"]:
                self.indicators[symbol]["hma"] = self.hma(symbol, self.hma_period)
                self.past_indicators[symbol]["hma"] = RollingWindow[float](self.past_indicators_win)
            #CMO
            if toggle_indicators["cmo"]:
                self.indicators[symbol]["cmo"] = self.cmo(symbol, self.cmo_period)
                self.past_indicators[symbol]["cmo"] = RollingWindow[float](self.past_indicators_win)
            #UO
            if toggle_indicators["uo"]:
                self.indicators[symbol]["uo"] = self.ultosc(symbol,
                                                            self.uo_short,
                                                            self.uo_mid,
                                                            self.uo_long)
                self.past_indicators[symbol]["uo"] = RollingWindow[float](self.past_indicators_win)

    def OnData(self, data):
        for crypto in self.cryptos:
            x_values = [[]]
            cur_price = self.securities[crypto].price

            #save indicator values + any modifications done here
            for key, indicator in self.indicators[crypto].items():
                if not indicator.is_ready:
                    # if self.time - self.prev_time >= timedelta(days=14):
                    #     self.prev_time = self.time
                    #     self.debug(f"Cur_time: {self.time}, Not Ready")
                    return
            
                if key == "macd":
                    macd = indicator.current.value - indicator.signal.current.value
                    self.past_indicators[crypto]["macd"].add(macd)
                elif key == "vwap":
                    vwap = cur_price - indicator.current.value
                    self.past_indicators[crypto]["vwap"].add(vwap)
                elif key == "rsi":
                    rsi = indicator.current.value
                    self.past_indicators[crypto]["rsi"].add(rsi)
                elif key == "adx":
                    adx = indicator.current.value
                    self.past_indicators[crypto]["adx"].add(adx)
                elif key == "cci":
                    cci = indicator.current.value
                    self.past_indicators[crypto]["cci"].add(cci)
                elif key == "stoch":
                    stoch = indicator.stoch_k.current.value - indicator.stoch_d.current.value
                    self.past_indicators[crypto]["stoch"].add(stoch)
                elif key == "hma":
                    hma = indicator.current.value
                    self.past_indicators[crypto]["hma"].add(hma)
                elif key == "cmo":
                    cmo = indicator.current.value
                    self.past_indicators[crypto]["cmo"].add(cmo)
                elif key == "uo":
                    uo = indicator.current.value
                    self.past_indicators[crypto]["uo"].add(uo)

            #putting all indicators in one vector
            for key, indicator in self.indicators[crypto].items():
                if self.past_indicators[crypto][key].count < self.past_indicators_win:
                    return
                for i in range(self.past_indicators_win):
                    x_values[0].append(self.past_indicators[crypto][key][i])

            #create prediction
            pred = self.models[self.symbol_to_tag[crypto]].predict(x_values)[0]
            self.past_signals[crypto].add(pred)

            self.debug(pred)

            avg_pred = pred
            # avg_pred = 0.0
            # for i in range(self.past_signals[crypto].count):
            #     avg_pred += self.past_signals[crypto][i]
            # avg_pred /= self.past_signals[crypto].count
            
            #make trade
            holdings = self.portfolio[crypto]
            cur_time = self.time
            #"short"
            if avg_pred == 0:
                if holdings.quantity >= 0:
                    self.prev_time = cur_time
                    self.boughtPrices[crypto] = cur_price
                    self.set_holdings(crypto, -self.fixed_invest)
            #long
            if avg_pred == 2:
                if holdings.quantity <= 0:
                    self.prev_time = cur_time
                    self.boughtPrices[crypto] = cur_price
                    self.set_holdings(crypto, self.fixed_invest)
            #stay
            else:
                if abs(holdings.quantity) >= 0.1:
                    if cur_price >= (1 + self.profit_margin) * self.boughtPrices[crypto]:
                        self.set_holdings(crypto, 0)
                    elif cur_price <= (1 - self.safety_margin) * self.boughtPrices[crypto]:
                        self.set_holdings(crypto, 0)
                    # elif self.time - self.prev_time >= self.cooldown:
                    #     self.set_holdings(crypto, 0)
