from utilities.utility import time_now,MARKET_CLOSE_TIME,MARKET_OPEN_TIME
import pandas as pd
from datetime import timedelta
import time
import os
import datetime as dt
from telegramBot.telegrambot import send_alert
class Strategy():
    def __init__(self, params, market_data,tick_data):
        # Set instance variables
        for keys,values in params.items():
            setattr(self,keys,values)
        self.market_data = market_data
        self.kite = market_data.kite
        self.tick_data = tick_data
        self.resampled_historical_data = self.get_historical_data()
        self.market_open_time = dt.datetime.strptime(MARKET_OPEN_TIME, "%H:%M").time()
        self.market_close_time = dt.datetime.strptime(MARKET_CLOSE_TIME, "%H:%M").time()
        self.buy_signal=False
        self.sell_signal=False
        self.entered=False
        self.current_position = None
        self.buy_sl=None
        self.sell_sl=None
        self.long_tsl=0
        self.short_tsl=7000
    def get_historical_data(self):
        """
        Gets historical OHLC data for the given instrument for last 10 days.

        Returns:
        - dataframe containing the historical OHLC data.
        """
        from_date = time_now().date() - timedelta(days=10)
        to_date = time_now().date()
        ohlc = self.market_data.kite1.historical_data(self.instrument_token, from_date, to_date, interval = 'minute')
        df = pd.DataFrame(ohlc)
        df['timestamp'] = pd.to_datetime(df['date']).dt.tz_localize(None)
        df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df.drop(['date','volume'],axis=1,inplace=True)
        df.set_index('timestamp', inplace=True)
        return df

    def calculate_ema(self, ema_period):
        """
        Calculates the EMA of close prices for the given period.

        args:
        - ema_period: The period for which the EMA needs to be calculated.

        Returns:
        - series containing the EMA values.
        """
        try:
            if not isinstance(ema_period, (int, float)):
                print("Error: EMA period must be a number.")
                return None
            if ema_period <= 0:
                print("Error: EMA period must be a positive number.")
                return None
            return round(self.historical_candle_data['close'].ewm(span=ema_period).mean(), 2)
        except:
            print("Error fetching EMA.")
        
    def run_strategy(self):
        # Get current time and historical candle data
        now = time_now()
        self.historical_candle_data = self.get_historical_data()
        # set candle interval depending on the timeframe
        candle_interval = 1 if self.timeframe == "1m" else None
        # Wait until market open time
        if now.time() < self.market_open_time:
            print("sleeping before market hours")
            time.sleep((dt.datetime.combine(dt.datetime.today(), self.market_open_time)-dt.datetime.combine(dt.datetime.today(), now.time())).total_seconds())
            now = time_now()
            # loop until market close time
            while self.market_open_time < now.time() < self.market_close_time:
                # calculate the next time to check for a signal
                next_run = now + timedelta(minutes=candle_interval)
                now = time_now()
                print(f'next_run {next_run}')

                # if the current time is before the next run time, sleep until the next run time
                if now < next_run:
                    print(f"sleeping for {(next_run - now).total_seconds()} seconds")
                    time.sleep((next_run - now).total_seconds())
                time.sleep(3)
                try:
                    retry_count = 0
                    while True:
                        if retry_count==3:
                            break
                        try:
                            df = pd.DataFrame(self.tick_data[self.instrument_token])
                            break
                        except:
                            # send_alert1(f'handling value error in {self.instrument}')
                            print(f'handling value error in {self.tradingsymbol}')
                            if retry_count < 3:
                                time.sleep(1)
                                retry_count += 1
                    candle_time = time_now().time()
                    # Resample tick data to candle data and append to historical candle data
                    df.set_index('timestamp', inplace=True)
                    resampled_df = df.resample(f'1T').ohlc()  # Get only the last resampled data
                    resampled_df = resampled_df.iloc[-(candle_interval+1):-1]#.to_frame().T
                    print(resampled_df)
                    resampled_df.columns = resampled_df.columns.droplevel()
                    self.historical_candle_data = pd.concat([self.historical_candle_data, resampled_df])
                    print(f'candle fetched at {candle_time}')
                    if os.path.isfile(f'./data/{self.tradingsymbol}_1min.csv'):
                        # Append to file
                        resampled_df.to_csv(f'./data/{self.tradingsymbol}_1min.csv', mode='a', header=False)
                    else:
                        # Create a new file
                        self.historical_candle_data.to_csv(f'./data/{self.tradingsymbol}_1min.csv', mode='w', header=True)
                    print(f'saved {self.tradingsymbol}_1min.csv file')
                    print(f"{self.tradingsymbol} LTP is {self.tick_data[self.instrument_token][-1]['ltp']} at {time_now().time()}")
                    
                except Exception as e:
                    print(e)
                    break
                # Calculate EMAs for different periods
                ema1 = self.calculate_ema(self.ema1).iloc[-1].item()
                ema2 = self.calculate_ema(self.ema2).iloc[-1].item()
                ema3 = self.calculate_ema(self.ema3).iloc[-1].item()
                print(ema1, ema2, ema3)
                if self.entered:
                    if self.current_position=='long':
                        if self.historical_candle_data.iloc[-1]['close']<ema3:
                            print(f"close is {self.historical_candle_data.iloc[-1]['close']} and ema3 is {ema3}")
                            self.long_tsl = self.historical_candle_data.iloc[-1]['close']
                            send_alert(f'LONG TSL SET TO {self.long_tsl}')
                    elif self.current_position=='short':
                        if self.historical_candle_data.iloc[-1]['close']>ema3:
                            print(f"close is {self.historical_candle_data.iloc[-1]['close']} and ema3 is {ema3}")
                            self.short_tsl = self.historical_candle_data.iloc[-1]['close']
                            send_alert(f'SHORT TSL SET TO {self.short_tsl}')
                current_time = time_now()
                print(ema1, ema2, ema3)
                if (ema1>ema2) and (ema2>ema3) and (self.current_position!='long') and (not self.buy_signal):
                    self.buy_signal = True
                    self.sell_signal=False
                    self.buy_trigger=self.historical_candle_data.iloc[-1]['high']
                    self.buy_sl = self.historical_candle_data.iloc[-1]['low']
                    send_alert(f'{self.tradingsymbol} BUY signal generated @ {time_now()} {self.buy_trigger}')
                elif (ema1<ema2) and (ema2<ema3) and (self.current_position!='short') and (not self.sell_signal):
                    self.sell_signal =True
                    self.buy_signal=False
                    self.sell_trigger=self.historical_candle_data.iloc[-1]['low']
                    self.sell_sl = self.historical_candle_data.iloc[-1]['high']
                    send_alert(f'{self.tradingsymbol} SELL signal generated @ {time_now()} {self.sell_trigger}')
                print(f'BUY {self.buy_signal} SELL {self.sell_signal}')
                if self.buy_signal:
                    print('checking for LONG')
                    while(current_time<next_run+timedelta(minutes=candle_interval)):
                        # print('checking for LONG')
                        time.sleep(1)
                        current_ltp = self.tick_data[self.instrument_token][-1]['ltp']
                        # print(self.buy_trigger, current_ltp)
                        if current_ltp > self.buy_trigger:
                            if self.current_position=='short':
                                send_alert(f"exiting short position @ {current_ltp}")
                                self.sell_sl=None
                            # self.buy_sl = self.historical_candle_data.iloc[-1]['low']
                            send_alert(f"Long @ {current_ltp} with SL {self.buy_sl}")
                            self.buy_signal=False
                            self.sell_signal=False
                            self.entered=True
                            self.current_position='long'
                            break
                        current_time=time_now()
                elif self.sell_signal:
                    print('checking for SHORT')
                    while(current_time<next_run+timedelta(minutes=candle_interval)):
                        # print('checking for SHORT')
                        time.sleep(1)
                        current_ltp = self.tick_data[self.instrument_token][-1]['ltp']
                        # print(self.sell_trigger, current_ltp)
                        if current_ltp < self.sell_trigger:
                            if self.current_position=='long':
                                send_alert(f"exiting long position @ {current_ltp}")
                                self.buy_sl=None
                            # self.sell_sl = self.historical_candle_data.iloc[-1]['high']
                            send_alert(f"Short @ {current_ltp} with SL {self.sell_sl}")
                            self.sell_signal=False
                            self.buy_signal=False
                            self.entered=True
                            self.current_position='short'
                            break
                        current_time = time_now()
                elif self.entered:
                    while(current_time<next_run+timedelta(minutes=candle_interval)):
                        print('Checking for SL')
                        time.sleep(1)
                        current_ltp = self.tick_data[self.instrument_token][-1]['ltp']
                        if self.current_position=='long':
                            if (current_ltp < self.buy_sl) or (current_ltp<self.long_tsl):
                                print(f'SL hit for LONG SIDE @{current_ltp}')
                                self.entered=False
                                self.current_position=None
                                self.buy_sl=None
                                self.long_tsl=0
                                break
                                
                        elif self.current_position=='short':
                            if (current_ltp > self.sell_sl) or (current_ltp>self.short_tsl):
                                print(f'SL hit for Short SIDE @{current_ltp}')
                                self.entered=False
                                self.current_position=None
                                self.sell_sl=None
                                self.short_tsl=7000
                                break
                        current_time = time_now()
                now = next_run
            

