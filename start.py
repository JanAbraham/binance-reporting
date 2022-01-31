"""main module, which brings the diifferent binance_reporting modules together

downloading all account information from exchange

This module is configured and controlled by a config file, which need to be provided when calling it

**currently available download functions:**
    - balances
    - history of trades
    - history of orders
    - open orders
    - deposits
    - withdrawals
    - daily snapshots

"""
import os
import sys
import logging

from binance_reporting import helper
from binance_reporting import downloader
from binance_reporting import ticker

# logging will start with default settings and on console
# after config is read, these will overwrite the default settings

log_file = "binance_reporting.log"
log_level = 'INFO'
log_target = ''
log_format="%(asctime)s [%(levelname)s] - [%(filename)s > %(funcName)s() > %(lineno)s] - %(message)s"
log_date_format = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=log_level,
    format=log_format, datefmt=log_date_format
    )

# reset logging to the right config as in config file

logging.info(" --- Start downloading data from Exchange ---")
logging.info(" ---- Loading config.")

config = helper.read_config(sys.argv)

if config == 0:
    logging.warning("Binance download aborted unsuccessful.")
    sys.exit("No config found. Aborting download from exchange.")

log_level = config['logging']['log_level']
log_file = config['logging']['log_file']
log_target = config['logging']['log_target']

if log_target == 'file':
    logging.basicConfig(
        level=log_level,
        filename=log_file,
        format=log_format, datefmt=log_date_format, force = True
        )
else:
    logging.basicConfig(
        level=log_level,
        format=log_format, datefmt=log_date_format, force = True
        )

logging.info(" --- Downloading all account information from Exchange ---")

data_dir = os.getcwd()
telegram_token = config['telegram']['token']

accounts = config['accounts']
account_groups = config['account_groups']

if config['modules']['balance_ticker']:
    ticker.send_bal(accounts, account_groups, telegram_token)

list_of_trading_pairs = helper.get_trading_pairs('USDT')

for account in accounts:
    logging.info(" -- start downloading data for account %s --", account)

    account_details = accounts[account]
    PUBLIC = os.environ.get(account_details['osvar_api_public'])
    SECRET = os.environ.get(account_details['osvar_api_secret'])

    file_directory = data_dir + "/" + account_details['dir'] + "/"
    if not os.path.exists(file_directory):
        os.makedirs(file_directory)
    open_orders_file = file_directory + "open_orders_" + account + ".csv"
    orders_file = file_directory + "orders_" + account + ".csv"
    trades_file = file_directory + "trades_" + account + ".csv"
    balances_file = file_directory + "balances_" + account + ".csv"
    bal_fut_positions_file = file_directory + "balances_" + account + "_positions.csv"
    bal_fut_assets_file = file_directory + "balances_" + account + "_assets.csv"
    prices_file = file_directory + "prices.csv"
    deposits_file = file_directory + "deposits_" + account + ".csv"
    withdrawals_file = file_directory + "withdrawals_" + account + ".csv"
    snapshots_balances_file = (file_directory + "snapshot_daily_" + account + "_balances.csv")
    snapshots_assets_file = (file_directory + "snapshot_daily_" + account + "_assets.csv")
    snapshots_positions_file = (file_directory + "snapshot_daily_" + account + "_positions.csv")

    writetype = "w"

    modules = config['modules']

    if modules['download_balances']: 
        downloader.balances(
            account, account_details['type'], PUBLIC, SECRET, balances_file, bal_fut_positions_file, bal_fut_assets_file, writetype)

    if modules['download_trades']:
        downloader.trades(
            account, account_details['type'], PUBLIC, SECRET, list_of_trading_pairs, trades_file)

    if modules['download_orders']:
        downloader.orders(account, account_details['type'], PUBLIC, SECRET, list_of_trading_pairs, orders_file)

    if modules['download_open_orders']:
        downloader.open_orders(account, account_details['type'], PUBLIC, SECRET, open_orders_file)

    if modules['download_deposits']:
        downloader.deposits(account, account_details['type'], PUBLIC, SECRET, deposits_file)

    if modules['download_withdrawals']:
        downloader.withdrawals(account, account_details['type'], PUBLIC, SECRET, withdrawals_file)

    if modules['download_daily_account_snapshots']:
        downloader.daily_account_snapshots(
            account,
            account_details['type'],
            PUBLIC,
            SECRET,
            snapshots_balances_file,
            snapshots_positions_file,
            snapshots_assets_file
        )

    if modules['download_prices']:
        downloader.prices(prices_file)

    logging.info(" -- Finished downloading all data for account %s --", account)

if modules['download_daily_account_snapshots']:
    logging.info(" -- Merging snapshot files from different accounts. --")
    targetfile = (data_dir + "/snapshots_daily_all_accounts.csv")
    sourcefiles = []
    for account in accounts:
        account_details = accounts[account]
        file_directory = data_dir + "/" + account_details['dir'] + "/"
        filename = (
            file_directory
            + "snapshot_daily_"
            + account
            + "_balances"
            + ".csv"
        )
        sourcefiles.append(filename)
    helper.merge_files(sourcefiles, targetfile)
    logging.info(" -- Merging snapshot files finished. --")

if modules['download_balances']:
    logging.info(" -- Merging balances files from different accounts. --")            
    targetfile = (data_dir + "/balances_all_accounts.csv")
    sourcefiles = []
    for account in accounts:
        account_details = accounts[account]
        file_directory = data_dir + "/" + account_details['dir'] + "/"
        filename = (
            file_directory
            + "balances_"
            + account
            + ".csv"
        )
        sourcefiles.append(filename)
    helper.merge_files(sourcefiles, targetfile)
    logging.info(" -- Merging snapshot files finished. --")

if modules['download_deposits']:
    logging.info(" -- Merging deposit files from different accounts. --")            
    targetfile = (data_dir + "/deposits_all_accounts.csv")
    sourcefiles = []
    for account in accounts:
        account_details = accounts[account]
        file_directory = data_dir + "/" + account_details['dir'] + "/"
        filename = (
            file_directory
            + "deposits_"
            + account
            + ".csv"
        )
        sourcefiles.append(filename)
    helper.merge_files(sourcefiles, targetfile)
    sourcefiles = [data_dir + '/deposits_all_accounts.csv', data_dir + '/withdrawals_all_accounts.csv']
    targetfile = data_dir + "/transfers_all_accounts.csv"
    helper.merge_files(sourcefiles, targetfile)
    logging.info(" -- Merging deposit files finished. --")

if modules['download_withdrawals']:
    logging.info(" -- Merging withdrawal files from different accounts. --")            
    targetfile = (data_dir + "/withdrawals_all_accounts.csv")
    sourcefiles = []
    for account in accounts:
        account_details = accounts[account]
        file_directory = data_dir + "/" + account_details['dir'] + "/"
        filename = (
            file_directory
            + "withdrawals_"
            + account
            + ".csv"
        )
        sourcefiles.append(filename)
    helper.merge_files(sourcefiles, targetfile)
    sourcefiles = [data_dir + '/deposits_all_accounts.csv', data_dir + '/withdrawals_all_accounts.csv']
    targetfile = data_dir + "/transfers_all_accounts.csv"
    helper.merge_files(sourcefiles, targetfile)
    logging.info(" -- Merging withdrawal files finished. --")
