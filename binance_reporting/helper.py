"""helper modules for binance-reporting library

**Modules available**
    - API close connection
    - API weight check and cool down if overheated
    - removing blank lines in csv files
    - get symbols from exchange
    - merging all files in a directory into one file
    - merging multiple files into one file
    - read configuration file (yaml)
"""
import os       # file & dir ops
import time     # sleep for API cool-off
import yaml     # read config file
import logging
from binance.client import Client       # read trading pairs from exchange
import pandas as pd

def read_config(args):
    """read config from a given file and convert it into a dictionary
    
    **Procedure**
        - read the default config hardcoded in the script
        - read config from given file (provided as argument)
        - update default config with config from file
        - give the dictionary with config infos back as a result

    :param list args: required; config file as provided when calling the script

    :returns: dictionary with config info
    """
    logging.debug(' - Set default configuration. -')

    config_default = {
        "modules" : {
            "balances": False,
            "daily_account_snapshots": False,
            "trades": False,
            "orders": False,
            "open_orders": False,
            "deposits": False,
            "withdrawals": False,
            "ticker": False,
            "prices": False,
            "klines": False},
        "accounts": {
            "Account1": {
            "dir": "dir1",
            "type": "SPOT",
            "osvar_api_public": "READ_PUBLIC_A1_SPOT",
            "osvar_api_secret": "READ_SECRET_A1_SPOT",
            "chat_pseudo": "A1",
            "chat_id": '@A1',
            "investment": 1000,
            "cash": 0,
            "portval": 0,
            "profit": 0},
            "Account2": {
            "dir": "dir2",
            "type": "FUTURES",
            "osvar_api_public": "READ_PUBLIC_A2_FUTURES",
            "osvar_api_secret": "READ_SECRET_A2_FUTURES",
            "chat_pseudo": "A2",
            "chat_id": '@S2',
            "investment": 2000,
            "cash": 0,
            "portval": 0,
            "profit": 0}},
        "account_groups": {
            "ALL": {
            "accounts": ["Account1", "Account2"],
            "chat_id": '@A3',
            "chat_pseudo": "all"}},
        "telegram": {
            "token": "<telegram-token>"},
        "logging": {
            "log_activate": True,
            "log_level": "INFO",
            "log_target": "console",
            "log_file" : "binance_reporting.log"},
        "klines": {
            "dir": "klines_data",
            "symbol": ['USDT'],
            "kline_interval": ['5m', '1d']},
        "daily_account_snapshots": {
            "snapshot_days_max": 180,
            "snapshot_days_per_request": 30}}

    logging.info(' - Read configuration file. -')
    config = 0
    
    if len(args) == 2:
        config_file = os.getcwd() + "/" + args[1]
        if os.path.isfile(config_file):
            logging.debug('Config file found! Reading ...')
            config = config_default
            with open(config_file, 'r') as file:
                config_diff = yaml.safe_load(file)
            logging.debug('Updating config with provided config.')
            config.update(config_diff)
            logging.debug('following configuration has been loaded: %s', config)
    else:
        if len(args) == 1:
            logging.warning("No config file provided. Please provide a config file, which is in the same directory from where you started this.")
        if len(args) == 2:
            logging.warning("No config file found: %s/%s", os.getcwd(), args[1])
        config = 0
        return config

    logging.info(' - Finished reading configuration. -')
    return config


def get_symbols(patterns:list = ['']):
    """get available trading pairs from exchange which contain a given string (e.g. USDT)

    **Goal**
        - reduce the amount of trading pairs to walk through, e.g. when downloading historic trades

    **Procedure**
        - get list of available trading pairs from exchange
        - filter the list according to pattern provided

    **Parameters**
        - no parameter = get all trading pairs
        - a string = trading pairs, which contain this string
        - a list of strings = trading pairs, which contain any of the strings in the list

    :param str or list pattern: required (if empty, all trading pairs will be returned)

    :returns: list of filtered trading pairs available on exchange
    """

    logging.debug("get list of Trading Pairs to download data about ...")
    client = Client()
    symbols_list = []

    # in case a string is given, change it into a list
    if type(patterns) == str:
        patterns = [patterns]

    # get all symbols from the exchange
    symbols_all = pd.DataFrame(client.get_all_tickers()).loc[:, ["symbol"]]

    # filter out pairs which are in the list of patterns

    for pattern in patterns:
        symbols = symbols_all[
            symbols_all.symbol.str.contains(pattern)]
        symbols = symbols["symbol"].values.tolist()
        symbols_list.extend(symbols)

    # remove duplicates & sort
    symbols_list = list(dict.fromkeys(symbols_list))
    symbols_list.sort()

    logging.debug(
        "Amount of Symbols with provided patterns available on exchange: %s", str(len(symbols_list)))

    return symbols_list


def API_weight_check(client):
    """verify current payload of Binance API and trigger cool-off if 75% of max payload is reached

    **Goal**
        - Avoiding errors while downloading data from binance.

    **Procedure**
        - check what the current payload is
        - if 75% of max payload has been reached, cool-off is initiated
        - send a keepalive signal for the api connection

    :param object client: required

    :returns: the payload value

    :TODO: read current max value for Payload from Binance config

    :TODO: SAPI API seems to have threshold of 12000 => incorporate those (discovered during snapshot downloads)
    """

    logging.debug("check payload of API")
    # customizable variables
    api_payload_threshold = 0.75  # Threshold is max 75%
    api_payload_limit = {
        "x-mbx-used-weight": 1200 * api_payload_threshold,
        "x-mbx-used-weight-1m": 1200 * api_payload_threshold,
        "X-SAPI-USED-IP-WEIGHT-1M": 12000 * api_payload_threshold,
    }

    # internal variables
    int_loop_counter = 0
    api_header_used = ""

    # find out which of the headers is used in the API calls
    for api_header in api_payload_limit:
        if api_header in client.response.headers:
            api_header_used = api_header

    # loop as long as api payload is above threshold
    while (
        int(client.response.headers[api_header_used])
        > api_payload_limit[api_header_used]
    ):
        int_loop_counter = int_loop_counter + 1
        logging.warning(
            "API overused! Waiting "
            + str(int_loop_counter)
            + "min for API to cool-off."
        )
        logging.debug("Payload = " + str(client.response.headers[api_header_used]))
        time.sleep(int_loop_counter * 60)
        # make sure the api connection stays alive during the cool-off period
        try:
            logging.debug("   ... sending keepalive signal to exchange.")
            logging.debug("api_header used before keep alive ping: " + api_header_used)
            listenkey = client.stream_get_listen_key()
            client.stream_keepalive(listenkey)
            # find out which of the headers is used in the API calls
            # this might change after keep alive ping
            for api_header in api_payload_limit:
                if api_header in client.response.headers:
                    api_header_used = api_header
            logging.debug("api_header used after keep alive ping: " + api_header_used)
        except Exception as e:
            logging.warning("Exception occured: ", exc_info=True)

    logging.debug(
        "Check payload of API finished. Current Payload is "
        + str(client.response.headers[api_header_used])
    )
    return client.response.headers[api_header_used]


def API_close_connection(client):
    """close API connection of a given client

    **Goal**
        - Avoid having left-over connections to the API to keep the environment neat and clean.

    **Procedure**
        - get listen key of client and close stream

    :param object client: required

    :returns: None

    :TODO: add different connection types for futures etc.
    """

    logging.debug("closing API connection")
    try:
        client.stream_close(client.stream_get_listen_key())
    except Exception as e:
        logging.warning("Exception occured: ", exc_info=True)
    logging.debug("API connection closed (if no error has been reported before)")


def file_remove_blanks(filename):
    """read csv file and remove blank lines
    
    **Goal**
        - Sometimes there are blank lines added to csv files when writing them in Windows. This function removes them.

    **Procedure**
        - load provided file into panda dataframe
        - dropping all empty rows from the dataframe
        - writing file back

    :param str filename: required; must include the complete absolute path to the file

    :returns: written csv file without empty rows
    """
    logging.info(" - removing blank rows from %s", filename)
    data = pd.read_csv(filename, skip_blank_lines=True, low_memory=False)
    data.dropna(how="all", inplace=True)
    data.to_csv(filename, header=True)
    logging.info(" - blank rows removed from %s", filename)


def merge_files(files_src: list, file_trgt: str):
    """merging all given files into one file

    **Goal**
        - creating one file with all records from different files for better usage in excel pivot tables
        - used to combine account information from different accounts into one file
        - being used for balances, withdrawals, deposits, snapshots

    **Procedure**
        - get a list of source files
        - loop through all files and append to target file

    :param list files_src: required; list of files, which should be merged

    :param str file_trgt: required; provides filename for merged csv file

    :returns: csv file with all the merged info
    """

    data = pd.DataFrame()
    data_new = pd.DataFrame()
    for file_src in files_src:
        if os.path.isfile(file_src):
            data_new = pd.read_csv(file_src)
            data = pd.concat([data, data_new])
            #data = data.append(data_new, ignore_index=True)
    data.to_csv(file_trgt, index=False)


def merge_klines(klines_dir_src : str, klines_dir_trgt : str, filename_trgt : str):
    """merging all klines files of a given directory into one file

    **Goal**
        - creating one file with all the klines of all trading-pairs for better usage in excel pivot tables
        - only being done for '1d' timeframes

    **Procedure**
        - get the source directory with all the kline csv files
        - loop through all files and append to target filename

    :param str klines_dir_src: required; provides complete path to source directory with all klines csv files
    :param str klines_dir_trgt: required; provides complete path to target directory for the merged csv files
    :param str filename_trgt: required; provides filename for merged csv file
    
    :returns: csv file with all the merged klines
    """

    logging.info("--- START --- Merging klines into one file ---")

    files = os.listdir(klines_dir_src)
    klines = pd.DataFrame()
    writemode = 'a'

    for f in files:
        if os.path.isfile(klines_dir_trgt + "/" + filename_trgt):
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
    logging.info("--- FINISHED --- Merging klines into one file ---")
