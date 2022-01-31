""" downloading historic ohlc data from exchange

Input:
    - trading pairs (as list)
    - kline interval

Output:
    - ohlc data
    - technical Indicators (currently RSI, WilliamsR and WRSI)

this data is used for backtesting (currently done in excel)

Procedure:
    - verify if kline data has been downloaded already previously
    - if so, determine the timestamp of the last read kline
    - check if new klines are available on the exchange
    - if so, add these to the existing klines if available
    - write ohlc data into a file per pair and kline interval
    - create new file for all data from 1d kline interval for use in excel

further information:
    - description of header for klines is documented 
      here: https://python-binance.readthedocs.io/en/latest/binance.html?highlight=get_historical_klines_generator#module-binance.client

TODO make usage of logging module rather than print statements
TODO incorporate into binance_reporting module
TODO work with config file
TODO align files in directory with available pairs (some pairs get de-listed, hence file can be deleted)
TODO only keep files for pairs, which have up-to-date data available; otherwise, just delete them
TODO sub-function for adding technical indicators to all files in a folder
 
"""
import os #used to find home directory for saving the files in dropbox
from binance import Client
import pandas as pd
from finta import TA        # for technical indicators
from binance_reporting import helper as hlp    # API weight check function
import logging

# customizable variables
kline_intervals = ['1d', '5m']#, '5m', '1h', '4h']#'1m', '1d'
trading_pairs = 'USDT' # if empty, then all trading pairs will be downloaded

#defining variables
if os.name == 'posix':
    home_dir = '/Users/' + os.environ['LOGNAME']
else:
    home_dir = os.environ['USERPROFILE']

file_directory = home_dir + '/dropbox/finance/binance/source data/history data/'

logfile = "binance_klines_download.log"
loglevel = "INFO"  #'INFO', 'DEBUG'
logging.basicConfig(
    level=loglevel,
    filename=logfile,
    format="%(asctime)s:%(levelname)s:%(module)s:%(lineno)d:\
    %(funcName)s:%(message)s",
)

def klines_merge(klines_dir_src : str, klines_dir_trgt : str, filename_trgt : str):
    """merging all klines files into into 1 file
    
    """
    logging.info("--- START --- Merging klines into one file ---")

    files = os.listdir(klines_dir_src)
    klines = pd.DataFrame()
    writemode = 'a'

    for f in files:
        if os.path.isfile(klines_dir_trgt + filename_trgt):
            writemode = 'a'
            headermode = False
        else:
            writemode = 'w'
            headermode = True
        logging.debug("..... adding filename: " + f)
        klines = pd.read_csv(klines_dir_src + "/" + f, skip_blank_lines=True, header=0 , usecols=[0,1,2,3,4,5], engine='python')
        klines['pair'] = f[f.rfind('_')+1:f.rfind('.')]
        logging.debug("... writing file ...")
        klines.to_csv(klines_dir_trgt + "/" + filename_trgt, header = headermode, index=False, mode = writemode)
        logging.debug("..... finished adding filename: " + f)
    logging.info("..... removing duplicates in target file, sort it and write ---")
    klines = pd.read_csv(klines_dir_trgt + "/" + filename_trgt)
    klines.drop_duplicates(subset=["open time", "pair"], keep="last", inplace=True)
    klines.sort_values(by=["pair", "open time"], inplace=True)
    klines.to_csv(klines_dir_trgt + "/" + filename_trgt, header = True, index = False, mode = 'w')
    logging.info("--- FINISHED --- Merging daily klines into one file ---")

logging.info("--- Start --- binance kline downloading ---")

logging.debug('connecting to binance ...')

# create the binance Client; no need for api key
client = Client("", "", {"timeout": 30})

# trading pairs can be customized
list_of_trading_pairs = []

# read all trading pairs
prices_df = pd.DataFrame(client.get_all_tickers())
list_of_trading_pairs = prices_df.loc[:, ['symbol']]
# filter trading pairs

if not trading_pairs == '':
    list_of_trading_pairs = list_of_trading_pairs[list_of_trading_pairs.symbol.str.contains(trading_pairs)]
    list_of_trading_pairs = list_of_trading_pairs['symbol'].values.tolist()

logging.info('... ' + str(len(list_of_trading_pairs)) + ' Trading Pairs found')
klines = pd.DataFrame()

for kline_interval in kline_intervals:
    paircount = 0
    history_file = file_directory + kline_interval + '/' + 'history_' + kline_interval + '_klines'
    for pair in list_of_trading_pairs:
        paircount = paircount + 1
        logging.info("--- START --- " + str(pair) + " --- " + kline_interval + " --- " + str(paircount) + " / " + str(len(list_of_trading_pairs)) + " ---")
        logging.debug('  ... verify previous downloads of historic data ...')
        history_file_pair = history_file + '_' + str(pair) +'.csv'
        k_time = 0
        if os.path.isfile(history_file_pair):
            logging.debug('  ... previous downloads found! Reading ...')
            klines = pd.read_csv(history_file_pair, header=0, skip_blank_lines=True, usecols=[0,1,2,3,4,5,6], skipfooter=1, engine='python')
            logging.debug('  ... ' + str(len(klines)) + ' Records found')
            if klines.empty: continue
            k_time = klines.iloc[-1, 6] + 1 #time of last entry
        else:
            logging.debug('  ... no previous downloads found!')
        k = pd.to_datetime(k_time, unit='ms') # datetime.utcfromtimestamp(k_time/1000).strftime('%d-%m-%y %H:%M:%S')
        logging.debug("  ... Time of last record: ", k)
        logging.debug('  ... Checking for new records ...')
        kline_new = pd.DataFrame(client.get_historical_klines_generator(pair, kline_interval, int(k_time)))
        if len(kline_new) < 2:
            logging.debug('  ... No new records available ...')
            continue
        logging.debug('  ... ' + str(len(kline_new)) + ' new Records found')
        kline_new = kline_new.drop([6,7,8,9,10,11], axis = 1)
        kline_new = kline_new.apply(pd.to_numeric)
        kline_new.columns = ['open time', 'open', 'high', 'low', 'close', 'volume']
        kline_new['open time ux'] = kline_new['open time']

        logging.debug('  ... adding new klines to existing klines (if available)')
        klines = klines.append(kline_new, ignore_index=True)
        klines['open time'] = pd.to_datetime(klines['open time ux'], unit='ms')
        klines.sort_values(by=['open time ux'], inplace=True)

        logging.debug('  ... adding technical indicators')
        klines['RSI'] = TA.RSI(klines, 14)
        klines['WilliamsR'] = TA.WILLIAMS(klines, 14)
        klines['WRSI'] = klines['RSI'] + klines['WilliamsR']
        klines['EMA50'] = TA.EMA(klines, period=50)
        klines['EMA100'] = TA.EMA(klines, period=100)
        klines['EMA200'] = TA.EMA(klines, period=200)
        klines['DEMA50'] = TA.DEMA(klines, period=50)
        klines['DEMA100'] = TA.DEMA(klines, period=100)
        klines['DEMA200'] = TA.DEMA(klines, period=200)

        logging.debug("  ... writing new records for " + str(pair))
        klines.to_csv(history_file_pair, index=False)
        logging.debug("  ... check API payload and wait for cool-off if necessary")
        hlp.API_weight_check(client)
        logging.info("--- FINISHED --- " + str(pair) + " --- " + kline_interval + " --- " + str(paircount) + " / " + str(len(list_of_trading_pairs)) + " ---")

    klines_merge(file_directory + '1d/', file_directory, 'history_1d_klines_all Assets.csv')

logging.info("--- Finished --- binance kline downloading ---")