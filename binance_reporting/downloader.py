"""Different functions for downloading and saving data from exchange.

functions available for:
    - history of trades
    - history of orders
    - open orders
    - deposits
    - withdrawals
    - daily snapshots
    - klines

:raises: SystemExit, in case config file has not been provided.

:TODO: add technical indicators to kline download
:TODO: re-work withdrawals equal to deposits (maybe merge them into one function 'transfers'? and create once csv file)
:TODO: standardize column names accross different files (e.g. insertTime vs. updateTime vs. updatetime or asset vs. coin)
:TODO: provide option for addresslist-translation-file to translate cryptic address names into human readable names and use it for deposits & withdrawals
:TODO: balances: add average entry price of open orders for locked assets + estimated exit value
"""
import os               # set home directory of current user depending on OS
import sys              # get arguments from calling the script
import time
import pandas as pd
from binance.client import Client
import logging
from finta import TA        # for technical indicators
try:
    from binance_reporting import helper as hlp
except:
    import helper as hlp

def balances(
    account_name: str,  # used to differentiate info in debug log
    account_type: str,
    PUBLIC: str,
    SECRET: str,
    balances_file: str = '',  # should include complete path
    bal_fut_positions_file: str = '',
    bal_fut_assets_file: str = '',
    writetype: str = 'w',  # 'a' or 'w'
    ):
    """download balances from exchange and write it into a csv file if provided

    **Procedure:**
        - check if account is SPOT or FUTURES (there are different data models behind these two)
        - add current USDT price for every asset in the balance
        - in case there is no USDT price found: '0' value will be filled in
        - save the data into the respective csv files (if provided), otherwise just return balance

    :param str account_name: required; added to csv file for easier tracking
    :param account_type: required. The type of the account.
    :type account_type: SPOT or FUTURE
    :param str PUBLIC: required; public part of API key to open connection to exchange
    :param SECRET: required; secret part of API key to open connection to exchange
    :param str balances_file: optional; name and location of the csv file to be filled with balances info (spot or futures)
    :param str bal_fut_positions_file: optional; name and location of the csv file to be filled with future positions info
    :param vbal_fut_assets_file: optional; name and location of the csv file to be filled with futures assets info
    :param str writetype: optional; indicates if balances should be added ('a') or a new file should be written ('w')
    
    :return:
        - writes csv file with balances of the account (if filenames have been provided)
        - the USD value of free & locked assets, cash available and the overall portfolio value
    :rtype: float64
    """
    logging.info(" - Start downloading balances for Account: %s -", account_name)
    logging.debug("connecting to binance ...")

    client = Client(api_key=PUBLIC, api_secret=SECRET)

    logging.debug("reading balances and prices from exchnge ...")
    hlp.API_weight_check(client)
    fut_pos = pd.DataFrame()
    fut_assets = pd.DataFrame()
    prices = pd.DataFrame(client.get_all_tickers())
    balances = pd.DataFrame()
    if account_type == "FUTURES":
        balances = pd.DataFrame()
        logging.debug('reading values for portval')
        accountinfo_fut = client.futures_account()
        hlp.API_close_connection(client)
        portval = {
            "asset": "PortVal",
            'totalInitialMargin' : accountinfo_fut['totalInitialMargin'],
            'totalMaintMargin' : accountinfo_fut['totalMaintMargin'], #needed for Ticker => check if we are close to Liquidation
            'totalWalletBalance' : accountinfo_fut['totalWalletBalance'], #needed for Ticker => Brutto Value
            'totalUnrealizedProfit' : accountinfo_fut['totalUnrealizedProfit'], #needed for Ticker => PnL
            'totalMarginBalance' : accountinfo_fut['totalMarginBalance'], #needed for Ticker => Balance
            'totalPositionInitialMargin' : accountinfo_fut['totalPositionInitialMargin'],
            'totalOpenOrderInitialMargin' : accountinfo_fut['totalOpenOrderInitialMargin'],
            'totalCrossWalletBalance' : accountinfo_fut['totalCrossWalletBalance'],
            'totalCrossUnPnl' : accountinfo_fut['totalCrossUnPnl'],
            'availableBalance' : accountinfo_fut['availableBalance'],
            'maxWithdrawAmount' : accountinfo_fut['maxWithdrawAmount'],
            'Asset value' : float(accountinfo_fut['totalWalletBalance']) + float(accountinfo_fut['totalUnrealizedProfit']),
            "updateTime": accountinfo_fut['updateTime'],
            'UTCTime' : pd.Timestamp("now")
        }
        portval = pd.DataFrame(portval, index=[0])
        balances = pd.concat([balances, portval], ignore_index=True)
    
        logging.debug("collecting future account positions and assets")
        fut_pos = pd.DataFrame(accountinfo_fut['positions'])
        fut_pos.drop(fut_pos[fut_pos.initialMargin == '0'].index, inplace = True)
        fut_pos['USDT price'] = 0
        for symbol in fut_pos["symbol"]:
            fut_pos["USDT price"].loc[fut_pos.symbol == symbol] = (prices["price"].loc[prices.symbol == symbol].iloc[0])
            fut_pos['UTCtime'] = pd.to_datetime(fut_pos["updateTime"], unit='ms', utc=True)
        fut_pos['account'] = account_name
        fut_pos['type'] = account_type
        logging.debug("collecting future account assets")

        fut_assets = pd.DataFrame(accountinfo_fut['assets'])
        fut_assets.drop(fut_assets[fut_assets.updateTime == 0].index, inplace=True)
        fut_assets['USDT price'] = 0
        for asset in fut_assets['asset']:
            if asset == 'USDT':
                price = 1
            else:
                price = prices["price"].loc[prices.symbol == asset + 'USDT'].iloc[0]
            fut_assets['USDT price'].loc[fut_assets.asset == asset] = price
      
        fut_assets[["marginBalance", "USDT price"]] = fut_assets[["marginBalance", "USDT price"]].apply(pd.to_numeric)
        fut_assets['Asset value'] = fut_assets['marginBalance'] * fut_assets['USDT price']
        portval = {
            "asset": ["PortVal"],
            "Asset value": [fut_assets["Asset value"].sum()],

        }
        portval = pd.DataFrame(portval)
        fut_assets = pd.concat([fut_assets, portval], ignore_index=True)

        fut_assets['UTCtime'] = pd.Timestamp("now")
        fut_assets['account'] = account_name
        fut_assets['type'] = account_type

        logging.debug("collect return values of function")
        result = {
            "updatetime": pd.Timestamp("now"),
            'maintmargin' : float(accountinfo_fut['totalMaintMargin']), #needed for Ticker => check if we are close to Liquidation
            'walletbalance' : float(accountinfo_fut['totalWalletBalance']), #needed for Ticker => Brutto Value
            'pnl' : float(accountinfo_fut['totalUnrealizedProfit']), #needed for Ticker => PnL
            'cash' : float(accountinfo_fut['totalMarginBalance']) - float(accountinfo_fut['totalMaintMargin']), #needed for Ticker => Balance
            "portval": float(balances["Asset value"].values[0])
        }
        if bal_fut_positions_file != '':
            logging.debug("write balances to %s", bal_fut_positions_file)
            fut_pos.to_csv(bal_fut_positions_file, index=False)
            fut_assets.to_csv(bal_fut_assets_file, index=False)

    if account_type == 'SPOT':
        accountinfo = client.get_account()
        hlp.API_close_connection(client)
        logging.debug("reducing lists of balances and prices to the minimum ...")
        balances = pd.DataFrame(accountinfo["balances"])
        balances[["free", "locked"]] = balances[["free", "locked"]].apply(pd.to_numeric)
        prices["price"] = pd.to_numeric(prices["price"])
        balances.drop(
            balances[(balances.free == 0) & (balances.locked == 0)].index, inplace=True
        )
        prices = prices[prices["symbol"].isin(balances["asset"] + "USDT")]

        logging.debug("adding USDT prices current date and to list")
        balances["USDT price"] = 0
        pd.set_option('mode.chained_assignment', None)
        for symbol in prices["symbol"]:
            balances["USDT price"].loc[balances.asset + "USDT" == symbol] = (
                prices["price"].loc[prices.symbol == symbol].iloc[0]
            )
        balances["USDT price"].loc[balances.asset == "USDT"] = 1

        logging.debug("calculate additional values for the balance overview")
        balances["Free Coin Value"] = balances["free"] * balances["USDT price"]
        balances["Locked Coin Value"] = balances["locked"] * balances["USDT price"]
        balances["Asset value"] = balances["Free Coin Value"] + balances["Locked Coin Value"]
        balances.sort_values(by=["asset"], inplace=True)
        if balances.loc[balances["asset"] == "USDT"].empty:
            free_coin_value = 0
        else:
            free_coin_value = balances["Free Coin Value"].loc[balances["asset"] == "USDT"].iloc[0]
        portval = {
            "asset": ['PortVal'],
            "Free Coin Value": [balances["Free Coin Value"].sum() - free_coin_value],
            "Locked Coin Value": [balances["Locked Coin Value"].sum()],
            "Asset value": [balances["Asset value"].sum()],
        }
        portval = pd.DataFrame(portval)
        balances = pd.concat([balances, portval], ignore_index=True)

        balances['updateTime'] = accountinfo['updateTime']
        balances["UTCTime"] = pd.Timestamp("now")

        logging.debug("collect return values of function")
        result = {
            "asset": "portval",
            "updatetime": balances['updateTime'],
            "UTCTime": balances["UTCTime"],
            "free_coin_value": portval["Free Coin Value"][0],
            "locked_coin": portval["Locked Coin Value"][0],
            "cash": free_coin_value,
            "portval": portval["Asset value"][0],
        }

    balances['account'] = account_name
    balances['type'] = account_type
    
    if balances_file != '':
        logging.debug("write balances to %s", balances_file)
        if writetype == "a":
            balances.to_csv(balances_file, index=False, header=False, mode=writetype)
        else:
            balances.to_csv(balances_file, index=False)

    logging.info(" - Finished downloading balances for account %s -", account_name)

    return result


def daily_account_snapshots(
    account_name,
    account_type,
    PUBLIC,
    SECRET,
    snapshots_balances_file,
    snapshots_positions_file,
    snapshots_assets_file
    ):
    """download daily account snapshots from exchange and write it into a csv file

    **Procedure:**
        - check if previous downloads exists, read them and determine the date of the last downloaded snapshot
        - walk through the assets of that day one-by-one to determine the close-price of that asset on the date of the snapshot
        - in case there is no price found: '0' value will be filled in
        - save the data into the respective csv files

    If you want to re-download all snapshots again, you just need to delete this file. Be cautious: Binance only holds max. 180 days of snapshots. In case you want to go back furhter, these
    days might be your only available information about older snapshots written by this procedure in case you have run it before. I recommend to save the previous version and add the missing dates manually into 
    the csv-file.

    adding some additional data to daily balances:
        - updatetime
        - USDT Price per asset from the date of the snapshot
        - PortVal = Value of all balances together from this day

    :param str account_name: required. The name of the account. Is used in csv exports.
    :param account_type: required. The type of the account.
    :type account_type: SPOT or FUTURE
    :param str PUBLIC: required. Public key of your exchange account
    :param str SECRET: required. Secret key of your exchange account
    :param str snapshot_balances_file: optional. filename (incl. absolute path), where the balances per day are exported to (in csv-format). For SPOT and FUTURE accounts.
    :param str snapshot_positions_file: optional. filename (incl. absolute path), where the positions per day are exported to (in csv-format). For FUTURE accounts only.
    :param str snapshot_assets_file: optional. filename (incl. absolute path), where the assets per day are exported to (in csv-format). For SPOT and FUTURE accounts.

    :return: portfolio value and written csv file(s) in case filename(s) have been provided
    :rtype: float64

    :TODO: make snapshot positions file an optional parameter
    """

    import math

    logging.info(" - Start downloading daily snapshots for account %s -", account_name)

    # customizable variables
    snapshot_days_max = 180  # Binance only saves snapshots only for last 180 days
    snapshot_days_per_request = 30  # amount of snapshot days per request to exchange

    # internal variables
    daily_ms = 86400000  # = milliseconds per day
    step_ms = daily_ms * snapshot_days_per_request
    snapshot_days_max_ms = snapshot_days_max * daily_ms
    current_time_ms = math.trunc(time.time() * 1000)  # current time in milliseconds
    pd.set_option('mode.chained_assignment', None)

    #
    # check if previous download is available and load it if so
    #
    logging.debug(
        "verify if csv file already exists and \
        determine last recorded snapshot"
    )
    snaps = pd.DataFrame()
    snaps_new = pd.DataFrame()
    snap_balances = pd.DataFrame()
    snap_assets = pd.DataFrame()
    snap_assets_new = pd.DataFrame()
    snap_positions = pd.DataFrame()
    snap_pos_new = pd.DataFrame()
    start_time_ms = current_time_ms - snapshot_days_max_ms
    if os.path.isfile(snapshots_balances_file):
        snap_balances = pd.read_csv(snapshots_balances_file)
        if not snap_balances.empty:
            start_time_ms = snap_balances["updateTime"].max() + 1
            if current_time_ms - start_time_ms < daily_ms:
                logging.info(" . No newer snapshot available.")
                logging.debug(" ... Date of last recorded snapshot is %s", str(pd.to_datetime(start_time_ms, unit="ms", utc=True)))
                return "No newer snapshot available."
            if os.path.isfile(snapshots_assets_file):
                snap_assets = pd.read_csv(snapshots_assets_file)

    #
    # download missing snapshots
    #
    logging.debug(" ... Opening connection to exchange.")
    client = Client(api_key=PUBLIC, api_secret=SECRET)
    # default value of 10 is too low for 30 days snapshot download per request
    client.REQUEST_TIMEOUT = 30
    logging.debug("download snapshots for Account %s", account_name)
    while start_time_ms < current_time_ms:
        logging.info(" . timeframe of snapshot download: %s to %s",
            str(pd.to_datetime(start_time_ms, unit="ms", utc=True)),
            str(pd.to_datetime(start_time_ms + step_ms, unit='ms', utc=True))
        )
        hlp.API_weight_check(client)
        try:
            snaps_new = pd.DataFrame(client.get_account_snapshot(
                    type=account_type,
                    startTime=int(start_time_ms),
                    endTime=int(start_time_ms + step_ms))
            )
        except Exception as e:
            logging.warning("Exception occured: ", exc_info=True)
            continue
        snaps = pd.concat([snaps, snaps_new], ignore_index=True)
        logging.info(" . overall nbr of snapshots downloaded: %s.", str(len(snaps)))
        start_time_ms = start_time_ms + step_ms + 1

    # get list of tickers and prices to add them later
    prices = pd.DataFrame(client.get_all_tickers())
    prices["price"] = pd.to_numeric(prices["price"])

    hlp.API_close_connection(client)

    #
    # split downloaded snapshots and add more data before writing it to csv file
    #
    logging.debug("writing snapshots to csv ...")
    if account_type == "SPOT":
        for snap in snaps["snapshotVos"]:
            updatetime_ms = snap["updateTime"]
            updatetime_utc = pd.to_datetime(snap["updateTime"], unit="ms", utc=True)
            snap_balance = pd.DataFrame(snap["data"]["balances"])
            snap_balance[["free", "locked"]] = snap_balance[["free", "locked"]].apply(
                pd.to_numeric
            )
            snap_balance.drop(
                snap_balance[(snap_balance.free == 0) & (snap_balance.locked == 0)].index, inplace=True
            )
            snap_balance["USDT symbol"] = snap_balance["asset"] + "USDT"
            snap_balance["USDT price"] = 0
            symbol_shortlist = prices[prices["symbol"].isin(snap_balance["asset"] + "USDT")]
            logging.info(" . add USDT prices to %s assets from snapshot of %s", str(len(symbol_shortlist)), str(updatetime_utc))
            for symbol in symbol_shortlist["symbol"]:
                try:
                    kline = pd.DataFrame(
                        client.get_historical_klines(
                            symbol,
                            Client.KLINE_INTERVAL_1DAY,
                            updatetime_ms,
                            updatetime_ms + daily_ms,
                            )
                        )
                except Exception as e:
                    logging.warning(" . API connection lost. Trying to re-connect and re-try.")
                    hlp.API_close_connection(client)
                    hlp.API_weight_check(client)
                logging.debug("downloading historic prices for %s. API payload: %s",
                    symbol,
                    str(hlp.API_weight_check(client))
                    )
                if not kline.empty:
                    snap_balance["USDT price"].loc[snap_balance["USDT symbol"] == symbol] = float(kline[4][0])
                else:
                    snap_balance["USDT price"].loc[snap_balance["USDT symbol"] == symbol] = 0
            snap_balance.drop("USDT symbol", inplace=True, axis=1)
            snap_balance["USDT price"].loc[snap_balance.asset == "USDT"] = 1
            logging.debug("calculate additional values for the balance overview")
            snap_balance["Free Coin Value"] = snap_balance["free"] * snap_balance["USDT price"]
            snap_balance["Locked Coin Value"] = snap_balance["locked"] * snap_balance["USDT price"]
            snap_balance["Asset value"] = (
                snap_balance["Free Coin Value"] + snap_balance["Locked Coin Value"]
            )
            snap_balance.sort_values(by=["asset"], inplace=True)
            snap_balance['updateTime'] = updatetime_ms
            if snap_balance.loc[snap_balance["asset"] == "USDT"].empty:
                free_coin_value = 0
            else:
                free_coin_value = snap_balance["Free Coin Value"].loc[snap_balance["asset"] == "USDT"].iloc[0]
            portval = {
                "asset": "PortVal",
                "Free Coin Value": snap_balance["Free Coin Value"].sum()- free_coin_value,
                "Locked Coin Value": snap_balance["Locked Coin Value"].sum(),
                "Asset value": snap_balance["Asset value"].sum(),
                "updateTime" : updatetime_ms
            }
            portval = pd.DataFrame(portval, index=[0])
            snap_balance = pd.concat([snap_balance, portval], ignore_index=True)

            #
            # write daily asset information into snapshot assets file
            # writing is done for every single snapshot to mitigate API timeouts without loosing the already downloaded snapshots
            # several date formatting actions to ensure
            # - UTCTime does not contain hh:mm:ss (for better handling in excel)
            # - no duplicates
            #
            snap_assets = pd.concat([snap_assets, snap_balance], ignore_index=True)
            snap_assets["UTCTime"] = pd.to_datetime(snap_assets['updateTime'], unit="ms", utc=True)
            snap_assets['UTCTime'] = pd.to_datetime(snap_assets['UTCTime'], format="%Y-%m-%d", utc=True, infer_datetime_format=True).dt.date
            snap_assets['UTCTime'] = pd.to_datetime(snap_assets['UTCTime'], format="%Y-%m-%d", utc=True, infer_datetime_format=True)
            snap_assets["account"] = account_name
            snap_assets["type"] = account_type
            snap_assets.drop_duplicates(
                    subset=["UTCTime", "asset", "account", "type"], keep="last", inplace=True
                    )
            snap_assets.to_csv(snapshots_assets_file, index=False, date_format="%Y-%m-%d")

            # writing daily balances
            snap_balances = pd.concat([snap_balances, portval], ignore_index=True)
            snap_balances["UTCTime"] = pd.to_datetime(snap_balances["updateTime"], unit="ms", utc=True)
            snap_balances['UTCTime'] = pd.to_datetime(snap_balances['UTCTime'], format="%Y-%m-%d", utc=True, infer_datetime_format=True).dt.date
            snap_balances['UTCTime'] = pd.to_datetime(snap_balances['UTCTime'], format="%Y-%m-%d", utc=True, infer_datetime_format=True)
            snap_balances["account"] = account_name
            snap_balances["type"] = account_type
            snap_balances.drop_duplicates(
                    subset=["UTCTime", "asset", "account", "type"], keep="last", inplace=True
                    )
            snap_balances.sort_values(by=['UTCTime'], ascending=False, inplace=True)
            snap_balances.to_csv(snapshots_balances_file, index=False, date_format="%Y-%m-%d")

    if account_type == "FUTURES":
        kline = pd.DataFrame()

        # load prev. positions / balances and assets have been loaded already
        if os.path.isfile(snapshots_positions_file):
            snap_positions = pd.read_csv(snapshots_positions_file)

        for snap in snaps["snapshotVos"]:
            updatetime_ms = snap["updateTime"]
            updatetime_utc = pd.to_datetime(snap["updateTime"], unit="ms", utc=True)

            snap_assets_new = pd.DataFrame(snap["data"]["assets"])
            snap_assets_new['USDT price'] = 0
            for asset in snap_assets_new['asset']:
                if asset == 'USDT':
                    price = 1
                else:
                    logging.info(" . downloading historic prices for %s. API payload: %s",
                        asset,
                        str(hlp.API_weight_check(client)))
                    kline = pd.DataFrame(
                        client.get_historical_klines(
                            asset + 'USDT',
                            Client.KLINE_INTERVAL_1DAY,
                            updatetime_ms,
                            updatetime_ms + daily_ms,
                        )
                    )
                    if not kline.empty:
                        price = float(kline[4][0])
                    else:
                        price = 0
                snap_assets_new["USDT price"].loc[snap_assets_new["asset"] == asset] = price
                
            # the order of following actions is important
            # some actions might appear double work, but it ensures consistent quality
            #
            # work on and save assets file
            snap_assets_new[["marginBalance", "walletBalance", "USDT price"]] = snap_assets_new[["marginBalance", "walletBalance", "USDT price"]].apply(pd.to_numeric)
            snap_assets_new['Margin value'] = snap_assets_new['marginBalance'] * snap_assets_new['USDT price']
            snap_assets_new['Wallet value'] = snap_assets_new['walletBalance'] * snap_assets_new['USDT price']
            snap_assets_new['PnL'] = snap_assets_new['marginBalance'] - snap_assets_new['walletBalance']
            snap_assets_new["Asset value"] = snap_assets_new['Margin value']
            portval = {
                "asset": "PortVal",
                "Margin value": snap_assets_new["Margin value"].sum(),
                "Wallet value": snap_assets_new["Wallet value"].sum(),
                "PnL" : snap_assets_new["PnL"].sum(),
                "Asset value": snap_assets_new["Margin value"].sum()}
            portval = pd.DataFrame(portval, index=[0])
            snap_assets_new = pd.concat([snap_assets_new, portval], ignore_index=True)
            snap_assets_new["updateTime"] = updatetime_ms
            snap_assets = pd.concat([snap_assets, snap_assets_new], ignore_index=True)
            snap_assets["UTCTime"] = pd.to_datetime(snap_assets["updateTime"], unit="ms", utc=True)
            snap_assets['UTCTime'] = pd.to_datetime(snap_assets['UTCTime'], format="%Y-%m-%d", utc=True, infer_datetime_format=True).dt.date
            snap_assets['UTCTime'] = pd.to_datetime(snap_assets['UTCTime'], format="%Y-%m-%d", utc=True, infer_datetime_format=True)
            snap_assets["account"] = account_name
            snap_assets["type"] = account_type
            snap_assets.drop_duplicates(
                    subset=["UTCTime", "asset", "account", "type"], keep="last", inplace=True)
            snap_assets.to_csv(snapshots_assets_file, index=False, date_format="%Y-%m-%d")

            # work on and save balances file
            snap_balances = snap_assets[snap_assets['asset'] == 'PortVal']
            snap_balances.drop(['marginBalance', 'walletBalance', 'USDT price'], axis=1, inplace=True)
            snap_balances.sort_values(by=['updateTime'], ascending=False, inplace=True)
            snap_balances.to_csv(snapshots_balances_file, index=False, date_format="%Y-%m-%d")

            # work on and save position file, case there are positions
            snap_pos_new = pd.DataFrame(snap["data"]["position"])
            if not snap_pos_new.empty:
                snap_pos_new[["entryPrice", "markPrice", "positionAmt", "unRealizedProfit"]] = snap_pos_new[["entryPrice", "markPrice", "positionAmt", "unRealizedProfit"]].apply(pd.to_numeric)
                snap_pos_new.drop(snap_pos_new[
                        (snap_pos_new.entryPrice == 0)
                        & (snap_pos_new.positionAmt == 0)
                        & (snap_pos_new.unRealizedProfit == 0)
                        ].index, inplace=True)
                snap_pos_new['USDT price'] = snap_pos_new['markPrice']
                snap_pos_new['entryValue'] = snap_pos_new['entryPrice'] * snap_pos_new['positionAmt']
                snap_pos_new['markValue'] = snap_pos_new['markPrice'] * snap_pos_new['positionAmt']
                snap_pos_new['ValueDiff'] = snap_pos_new['markValue'] - snap_pos_new['entryValue']
                posval = {
                    "symbol": "PosVal",
                    "unRealizedProfit": snap_pos_new["unRealizedProfit"].sum(),
                    "entryValue": snap_pos_new["entryValue"].sum(),
                    "markValue": snap_pos_new["markValue"].sum(),
                    "ValueDiff": snap_pos_new["ValueDiff"].sum()}
                posval = pd.DataFrame(posval, index=[0])
                snap_pos_new = pd.concat([snap_pos_new, posval], ignore_index=True)
                snap_pos_new["updateTime"] = updatetime_ms
                snap_positions = pd.concat([snap_positions, snap_pos_new], ignore_index=True)
                snap_positions["UTCTime"] = pd.to_datetime(snap_positions["updateTime"], unit="ms", utc=True)
                snap_positions['UTCTime'] = pd.to_datetime(snap_positions['UTCTime'], format="%Y-%m-%d", utc=True, infer_datetime_format=True).dt.date
                snap_positions['UTCTime'] = pd.to_datetime(snap_positions['UTCTime'], format="%Y-%m-%d", utc=True, infer_datetime_format=True)
                snap_positions["account"] = account_name
                snap_positions["type"] = account_type
                snap_positions.drop_duplicates(
                        subset=["UTCTime", "symbol", "account", "type"], keep="last", inplace=True
                        )
                snap_positions.to_csv(snapshots_positions_file, index=False, date_format="%Y-%m-%d")
        
    logging.info(" - Finished writing daily snapshots for account: %s -", account_name)


def trades(
    account_name, account_type, PUBLIC, SECRET, list_of_trading_pairs, trades_file
    ):
    """get trades and write them to csv file

    **Procedure:**
        - check if account is SPOT or FUTURES (there are different data models behind these two)
        - verify if file already exists and determine last recorded trade
        - loop through provided trading pairs and download historic trades if available
        - save the downloaded trades to csv file

    :param str account_name: required; added to csv file for easier tracking
    :param account_type: required. The type of the account.
    :type account_type: SPOT or FUTURE
    :param str PUBLIC: required; public part of API key to open connection to exchange
    :param SECRET: required; secret part of API key to open connection to exchange
    :param list list_of_trading_pairs: required; list of trading pairs for which trades should be downloaded; if list is empty, every trading pair is being checked (there are over 2k trading pairs, so this can take a while)
    :param str trades_file: required; name and location of the csv file to be filled with historic trades
    
    :return: writes csv file with historic trades of the provided account
    :rtype: csv file

    :TODO: include trades for FUTURES accounts as well 
    """
    if account_type == "FUTURES":
        result = "Sorry, future accounts are not yet supported by this procedure."
        return result
            
    trades = pd.DataFrame()
    last_rec_trade_time = 0
    if os.path.isfile(trades_file):
        trades = pd.read_csv(trades_file)

    new_trades = []

    logging.info(" - Start downloading trades for account: %s -", account_name)
    logging.debug("connecting to binance ...")

    # open connection to exchange
    client = Client(api_key=PUBLIC, api_secret=SECRET)

    for trading_pair in list_of_trading_pairs:
        logging.debug(
            "reading trades from Binance for Trading Pair %s ...", trading_pair)
        hlp.API_weight_check(client)
        # find out last recorded trade for this trading pair
        if trades.empty:
            last_rec_trade_time = 0
        else:
            last_rec_trade_time = trades[trades.symbol == trading_pair].time.max()
        if last_rec_trade_time > 0:
            trade_time = last_rec_trade_time
        else:
            trade_time = 0
        try:
            # read very last trade from binance with for trading pair (if any)
            last_trade = client.get_my_trades(symbol=trading_pair, limit=1)
            # check if there has been any trade at all for this trading pair; if not, go to the next trading pair
            if len(last_trade) == 0:
                continue
            # read timestamp of last trade on binance
            last_trade_time = last_trade[-1]["time"]
            # only read further trades from binance if they are not recorded yet in the csv file
            while trade_time < last_trade_time:
                # read new trades, which are not yet in the csv file
                new_trades.extend(
                    client.get_my_trades(symbol=trading_pair, startTime=trade_time)
                )
                # read timestamp of last downloaded record from binance
                trade_time = new_trades[-1]["time"]
            logging.debug("  ... overall amount of not yet recorded trades read: %s",
                str(len(new_trades)))
            logging.debug("  ... be gentle with the API and wait for 1sec")
            time.sleep(1)
        except Exception as e:
            logging.warning("Exception occured: ", exc_info=True)
            continue

    logging.debug("Amount of new Trading Records to be written: %s", str(len(new_trades)))
    hlp.API_close_connection(client)

    # only write trades into csv file if there have been new trades found
    if not len(new_trades) == 0:
        # adding new trades to existing list of trades from csv
        new_trades = pd.DataFrame(new_trades)
        trades = pd.concat([trades, new_trades], ignore_index=True)
        # add column with timestamp in a human readable format
        trades["UTCTime"] = pd.to_datetime(trades["time"], unit="ms", utc=True)
        trades.sort_values(by=["time"], inplace=True, ascending=False)

        logging.debug("writing trades to csv ...")
        trades.to_csv(trades_file, index=False)

    logging.info(
        " - Finished writing %s Trades for account %s -", 
        str(len(new_trades)),
        account_name)


def orders(
    account_name, account_type, PUBLIC, SECRET, list_of_trading_pairs, orders_file
    ):
    """get orders and write them to csv file

    **Procedure:**
        - check if account is SPOT or FUTURES (there are different data models behind these two)
        - verify if file already exists and determine last recorded order
        - loop through provided trading pairs and download historic orders if available
        - save the downloaded orders to csv file

    :param str account_name: required; added to csv file for easier tracking
    :param account_type: required. The type of the account.
    :type account_type: SPOT or FUTURE
    :param str PUBLIC: required; public part of API key to open connection to exchange
    :param SECRET: required; secret part of API key to open connection to exchange
    :param list list_of_trading_pairs: required; list of trading pairs for which orders should be downloaded; if list is empty, every trading pair is being checked (there are over 2k trading pairs, so this can take a while)
    :param str orders_file: required; name and location of the csv file to be filled with historic orders
    
    :return: writes csv file with historic orders of the provided account
    :rtype: csv file

    :TODO: include orders for FUTURES accounts as well 
    """
    logging.info(" - Start downloading orders for account: %s -", account_name)
    logging.debug("connecting to binance ...")

    if account_type == "FUTURES":
        result = "Sorry, future accounts are not yet supported by this procedure."
        return result
        
    client = Client(api_key=PUBLIC, api_secret=SECRET)

    #
    # get orders and write them to csv file
    #
    # verify if file already exists and determine last recorded order

    orders = pd.DataFrame()
    last_rec_order_time = 0
    if os.path.isfile(orders_file):
        orders = pd.read_csv(orders_file)

    new_orders = []
    for trading_pair in list_of_trading_pairs:
        logging.debug("reading orders from Binance for Trading Pair %s ...", trading_pair)
        hlp.API_weight_check(client)
        # find out last recorded order for this trading pair
        if orders.empty:
            last_rec_order_time = 0
        else:
            last_rec_order_time = orders[orders.symbol == trading_pair].time.max()

        if last_rec_order_time > 0:
            order_time = last_rec_order_time
        else:
            order_time = 0
        try:
            # read very last order from binance with for trading pair (if any)
            last_order = client.get_all_orders(symbol=trading_pair, limit=1)
            # check if there has been any order at all for this trading pair; if not, go to the next trading pair
            if len(last_order) == 0:
                continue
            # read timestamp of last order on binance
            last_order_time = last_order[-1]["time"]
            # only read further orders from binance if they are not recorded yet in the csv file
            while order_time < last_order_time:
                # read new orders, which are not yet in the csv file
                new_orders.extend(
                    client.get_all_orders(symbol=trading_pair, startTime=order_time)
                )
                # read timestamp of last downloaded record from binance
                order_time = new_orders[-1]["time"]
            logging.debug("  ... overall amount of not yet recorded orders: %s",
                str(len(new_orders)))
            logging.debug("  ... be gentle with the API and wait for 1 sec")
            time.sleep(1)
        except Exception as e:
            logging.warning("Exception occured: ", exc_info=True)
            continue

    logging.debug("Amount of new Order Records to be written: %s", str(len(new_orders)))
    hlp.API_close_connection(client)

    # only write orders into csv file if there have been new orders found
    if not len(new_orders) == 0:
        # adding new orders to existing list of orders from csv
        new_orders = pd.DataFrame(new_orders)
        orders = pd.concat([orders, new_orders], ignore_index=True)
        # change format of timestamp to human readable format
        orders["UTCTime"] = pd.to_datetime(orders["time"], unit="ms", utc=True)
        orders.sort_values(by=["time"], inplace=True, ascending=False)

        logging.debug("writing orders to csv ...")
        orders.to_csv(orders_file, index=False)
        logging.debug("Finished writing Orders!")

    logging.info(" - Finished writing %s orders for account %s -",
        str(len(new_orders)), account_name)


def open_orders(account_name, account_type, PUBLIC, SECRET, open_orders_file):
    """get open orders and write them to csv file

    **Procedure:**
        - check if account is SPOT or FUTURES (there are different data models behind these two)
        - connect to exchange and download all open orders
        - save the downloaded open orders to csv file

    :param str account_name: required; added to csv file for easier tracking
    :param account_type: required. The type of the account.
    :type account_type: SPOT or FUTURE
    :param str PUBLIC: required; public part of API key to open connection to exchange
    :param SECRET: required; secret part of API key to open connection to exchange
    :param str open_orders_file: required; name and location of the csv file to be filled with the open orders
    
    :return: writes csv file with open orders of the provided account
    :rtype: csv file

    :TODO: include open orders for FUTURES accounts as well
    """
    logging.info(" - Start downloading open orders for account: %s -", account_name)
    logging.debug("connecting to binance ...")

    if account_type == "FUTURES":
        result = "Sorry, future accounts are not yet supported by this procedure."
        return result
        
    client = Client(api_key=PUBLIC, api_secret=SECRET)
    hlp.API_weight_check(client)

    logging.debug("reading all open orders from Binance ...")
    open_orders = pd.DataFrame(client.get_open_orders())
    if not open_orders.empty:
        logging.debug("change timestamps in the open orders to a readable format ...")
        # add column with timestamp in a human readable format
        open_orders["UTCTime"] = pd.to_datetime(open_orders["time"], unit="ms", utc=True)
        # sorting open orders for time descending

    hlp.API_close_connection(client)
    logging.debug("writing open orders to csv ...")
    open_orders.to_csv(open_orders_file, index=False)
    logging.info(" - finished writing open orders to csv for account: %s -", account_name)


def deposits(account_name, account_type, PUBLIC, SECRET, deposits_file):
    """download account deposits from exchange and write them into a csv file

    Procedure:
        - check if account is SPOT or FUTURES (there are different data models behind these two)
        - verify if file already exists and determine last recorded deposit
        - For every deposit, following data is being added to the downloaded data from the exchange:
            - USDT price of the asset (close price from the day of transaction)
            - In case of the price of the coin is not available anymore, '0' value is being filled in.
            - overall value of coins in USDT from the day of the transaction
            - time of transaction in UTC format
        - save the downloaded deposits to csv file

    :param str account_name: required; added to csv file for easier tracking
    :param account_type: required. The type of the account.
    :type account_type: SPOT or FUTURE
    :param str PUBLIC: required; public part of API key to open connection to exchange
    :param SECRET: required; secret part of API key to open connection to exchange
    :param str deposits_file: required; name and location of the csv file to be filled with the deposits

    :return:
        - writes csv file with deposits of the binance account
        - dataframe with all deposits

    :TODO: add deposits for Futures Account
    """

    logging.info(" - Start downloading deposits for account %s -", account_name)

    # customizable variables
    start_time_ms = 1498870800000  # 1.July 2017 GMT; binance exchange went online for public trading on 12.07.2017

    # internal variables
    step_ms = 7776000000  # = 90 days; Binance does only allow to get deposit and withdraw data for 90 days timeframe
    klines_step_ms = 86400000  # for downloading asset price at the time of deposit
    current_time_ms = int(time.time() * 1000)  # current time in milliseconds

    if account_type == "FUTURES":
        result = "Sorry, future accounts are not yet supported by this procedure."
        return result
        
    deposits = pd.DataFrame()
    # fetch list of already downloaded deposits
    if os.path.isfile(deposits_file):
        deposits = pd.read_csv(deposits_file)
        if not deposits.empty:
            start_time_ms = int(deposits.insertTime.max() + 1)

    # fetch list of new deposits, if any
    logging.debug("connecting to binance ...")

    client = Client(api_key=PUBLIC, api_secret=SECRET)
    client.REQUEST_TIMEOUT = 10

    deposits_new = pd.DataFrame()
    while start_time_ms < current_time_ms:
        hlp.API_weight_check(client)
        deposits_new = pd.concat([deposits_new, 
            pd.DataFrame(
                client.get_deposit_history(
                    startTime=start_time_ms, endTime=start_time_ms + step_ms
                )
            )],
            ignore_index=True,
        )
        start_time_ms = start_time_ms + step_ms + 1

    # work with downloaded deposits, if any
    if not deposits_new.empty:
        prices = pd.DataFrame(
            client.get_all_tickers()
        )  # get list of tickers and prices
        prices["price"] = pd.to_numeric(prices["price"])
        logging.debug(" ... add USDT prices to deposited assets")
        deposits_new["USDT symbol"] = deposits_new["coin"] + "USDT"
        deposits_new[["USDT price", "Asset value"]] = 0
        symbol_shortlist = prices[prices["symbol"].isin(deposits_new["coin"] + "USDT")]
        deposits_shortlist = deposits_new[
            deposits_new["USDT symbol"].isin(symbol_shortlist["symbol"])
        ]
        for ind in deposits_shortlist.index:
            symbol = deposits_shortlist["USDT symbol"][ind]
            updatetime_ms = deposits_shortlist["insertTime"][ind]
            endtime_ms = updatetime_ms + klines_step_ms
            logging.debug(
                "downloading historic prices for %s. API payload: %s",
                symbol, str(hlp.API_weight_check(client)))
            kline = pd.DataFrame(
                client.get_historical_klines(
                    symbol, "1d", str(updatetime_ms), str(endtime_ms)
                )
            )
            deposits_new["USDT price"].loc[
                (deposits_new.insertTime == updatetime_ms)
                & (deposits_new["USDT symbol"] == symbol)
            ] = float(kline[4][0])
        hlp.API_close_connection(client)

        deposits_new.drop(["USDT symbol"], inplace=True, axis=1)
        deposits = pd.concat([deposits, deposits_new], ignore_index=True)
        logging.debug("calculate additional values for the deposits overview")
        deposits["USDT price"].loc[deposits.coin == "USDT"] = 1
        deposits[["amount", "USDT price", "Asset value"]] = deposits[
            ["amount", "USDT price", "Asset value"]
        ].apply(pd.to_numeric)
        deposits["Asset value"] = deposits["amount"] * deposits["USDT price"]
        deposits["UTCTime"] = pd.to_datetime(deposits["insertTime"], unit="ms", utc=True)
        deposits.sort_values(by=["insertTime"], inplace=True)
        deposits.drop_duplicates(subset=["txId"], keep="last", inplace=True)
        deposits['account'] = account_name
        deposits['type'] = account_type
        deposits['transaction'] = 'DEPOSIT'

        logging.debug("writing deposits to csv ...")
        deposits.to_csv(deposits_file, index=False)

    logging.info(" - Finished writing deposits for account: %s -", account_name)
    return deposits


def withdrawals(account_name, account_type, PUBLIC, SECRET, withdrawals_file):
    """download account withdrawals from exchange and write them into a csv file

    Procedure:
        - check if account is SPOT or FUTURES (there are different data models behind these two)
        - verify if file already exists and determine last recorded withdrawal
        - For every withdrawal, following data is being added to the downloaded data from the exchange:
            - USDT price of the asset (close price from the day of transaction)
            - In case of the price of the coin is not available anymore, '0' value is being filled in.
            - overall value of coins in USDT from the day of the transaction
            - time of transaction in UTC format
        - save the downloaded withdrawals to csv file

    :param str account_name: required; added to csv file for easier tracking
    :param account_type: required. The type of the account.
    :type account_type: SPOT or FUTURE
    :param str PUBLIC: required; public part of API key to open connection to exchange
    :param SECRET: required; secret part of API key to open connection to exchange
    :param str withdrawals_file: required; name and location of the csv file to be filled with the withdrawals

    :return:
        - writes csv file with withdrawals of the binance account
        - dataframe with all withdrawals

    :TODO: add withdrawals for Futures Account
    """
    logging.info(" - Start downloading withdrawals for account: %s -", account_name)

    # customizable variables
    start_time_ms = 1498870800000  # 1.July 2017 GMT; binance exchange went online for public trading on 12.07.2017

    # internal variables
    step_ms = 7776000000  # = 90 days; Binance does only allow to get deposit and withdraw data for 90 days timeframe
    klines_step_ms = 86400000  # for downloading asset price at the time of deposit
    current_time_ms = int(time.time() * 1000)  # current time in milliseconds

    if account_type == "FUTURES":
        result = "Sorry, future accounts are not yet supported by this procedure."
        return result
        
    transactions = pd.DataFrame()
    # fetch list of already downloaded transactions
    if os.path.isfile(withdrawals_file):
        transactions = pd.read_csv(withdrawals_file)
        if not transactions.empty:
            start_time_ms = int(transactions.insertTime.max() + 1)

    # fetch list of new transactions, if any
    logging.debug("connecting to binance ...")

    client = Client(api_key=PUBLIC, api_secret=SECRET)
    client.REQUEST_TIMEOUT = 10

    transactions_new = pd.DataFrame()
    while start_time_ms < current_time_ms:
        hlp.API_weight_check(client)
        transactions_new = pd.concat([transactions_new, 
            pd.DataFrame(
                client.get_withdraw_history(
                    startTime=start_time_ms, endTime=start_time_ms + step_ms
                )
            )],
            ignore_index=True,
        )
        start_time_ms = start_time_ms + step_ms + 1

    # work with downloaded transactions, if any
    if not transactions_new.empty:
        # adding a column with 'insertTime', containing epoch time, to be
        # aligned with the deposit downloads and re-using the same logic
        prices = pd.DataFrame(
            client.get_all_tickers()
        )  # get list of tickers and prices
        prices["price"] = pd.to_numeric(prices["price"])
        logging.debug("add USDT prices to deposited assets")
        transactions_new["USDT symbol"] = transactions_new["coin"] + "USDT"
        transactions_new[["USDT price", "Asset value"]] = 0.00
        transactions_new["insertTime"] = pd.to_datetime(transactions_new["applyTime"], utc=True)
        transactions_new["insertTime"] = (
            transactions_new["insertTime"].astype("int64") // 1e9 * 1000
        )
        symbol_shortlist = prices[
            prices["symbol"].isin(transactions_new["coin"] + "USDT")
        ]
        transactions_shortlist = transactions_new[
            transactions_new["USDT symbol"].isin(symbol_shortlist["symbol"])
        ]
        for ind in transactions_shortlist.index:
            symbol = transactions_shortlist["USDT symbol"][ind]
            updatetime_ms = int(transactions_shortlist["insertTime"][ind])
            endtime_ms = updatetime_ms + klines_step_ms
            logging.debug(
                "downloading historic prices for %s. API payload: %s",
                symbol, str(hlp.API_weight_check(client)))
            kline = pd.DataFrame(
                client.get_historical_klines(
                    symbol, "1d", str(updatetime_ms), str(endtime_ms)
                )
            )
            transactions_new["USDT price"][ind] = float(kline[4][0])
            # transactions_new['USDT price'].loc[(transactions_new.insertTime == updatetime_ms) & (transactions_new['USDT symbol'] == symbol)] = float(kline[4][0])
        hlp.API_close_connection(client)

        transactions_new.drop(["USDT symbol"], inplace=True, axis=1)
        transactions = pd.concat([transactions, transactions_new], ignore_index=True)
        logging.debug("calculate additional values for the transactions overview")
        # difference between deposits and withdrawals:
        #   - additional column 'transactionFee'
        #   - 'transactionFee' needs to be added to 'amount' when calculating the coin value
        transactions["USDT price"].loc[transactions.coin == "USDT"] = 1
        transactions[
            ["amount", "transactionFee", "USDT price", "Asset value"]
        ] = transactions[
            ["amount", "transactionFee", "USDT price", "Asset value"]
        ].apply(
            pd.to_numeric
        )
        transactions["Asset value"] = (
            transactions["amount"] + transactions["transactionFee"]
        ) * transactions["USDT price"] * -1
        transactions["UTCTime"] = pd.to_datetime(transactions["insertTime"], unit="ms", utc=True)
        transactions.sort_values(by=["insertTime"], inplace=True)
        transactions.drop_duplicates(subset=["id"], keep="last", inplace=True)

        transactions['account'] = account_name
        transactions['type'] = account_type
        transactions['transaction'] = 'WITHDRAWAL'
        logging.debug("writing transactions to csv ...")
        transactions.to_csv(withdrawals_file, index=False)

    logging.info(" - Finished writing withdrawals for account %s -", account_name)
    return transactions


def prices(prices_file):
    """read prices for all trading pairs and write them to prices.csv file

    Procedure:
        - connect to exchange and download all prices
        - save the downloaded prices to csv file

    :param str prices_file: required; name and location of the csv file to be filled with the prices

    :return: writes csv file with prices of all trading pairs on the exchange
    """
    logging.info(" - Start downloading prices for all trading pairs from exchange -")
    logging.debug("connecting to binance ...")

    client = Client()

    logging.debug("reading all prices from Binance ...")
    prices = pd.DataFrame(client.get_all_tickers())
    logging.debug("writing prices to csv ...")
    prices.to_csv(prices_file, index=False)
    logging.info(" - Finished writing Prices to csv! -")


def klines(dir, symbols, intervals, indicators, indicators_config):
    """ downloading historic ohlc data from exchange

    **Procedure:**
        - verify if kline data has been downloaded already previously
        - if so, determine the timestamp of the last read kline
        - check if new klines are available on the exchange
        - if so, add these to the existing klines if available
        - write ohlc data into a file per pair and kline interval
        - create new file for all data from 1d kline interval for use in excel

    :param str dir: required; name and location of the directory where the date should be written to
    :param list symbols: required. list of trading pairs for which the klines should be downloaded for
    :param list intervals: required; list of intervals (e.g. 1m, 5m, 1d) for which the klines should be downloaded for
    :param str indicators: optional; indicators, which should be added to the csv file
    :param str indicators_config: optional; parameters for the indicators, if required
    
    :return: writes csv files with downloaded klines and technical indicators (one file for each provided symbol)
    :rtype: csv file

    This data can be used for backtesting (currently done in excel)

    .. note:: Indicators are not yet implemented

    Further information: description of headers for klines is documented here: https://python-binance.readthedocs.io/en/latest/binance.html?highlight=get_historical_klines_generator#module-binance.client

    :TODO: klines: avoid downloading klines for pairs which dont provide up-to-date data anymore (e.g. last entry is longer ago than 10 times the selected timeframe)
    :TODO: klines: cleanup files, which dont have up-to-date data anymore
    :TODO: adding technical indicators after downloading klines according to config file
    """
    # internal variables
    klines = pd.DataFrame()

    logging.info("--- Start --- binance kline downloading ---")

    logging.debug('---- connecting to binance ...')

    # create the binance Client; no need for api key
    client = Client("", "", {"timeout": 30})

    logging.info('---- downloading klines of %s Trading pairs ...', str(len(symbols)))

    for interval in intervals:
        paircount = 0
        klines_file = dir + '/' + interval + '/' + 'history_' + interval + '_klines'
        if not os.path.exists(dir + '/' + interval):
            os.makedirs(dir + '/' + interval)
        for pair in symbols:
            paircount = paircount + 1
            logging.info("---- START --- %s --- %s --- %s / %s ---", str(pair), interval, str(paircount), str(len(symbols)))
            logging.debug('  ... verify previous downloads of historic data ...')
            history_file_pair = klines_file + '_' + str(pair) +'.csv'
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
            logging.debug("  ... Time of last record: %s", str(k))
            logging.debug('  ... Checking for new records ...')
            kline_new = pd.DataFrame(client.get_historical_klines_generator(pair, interval, int(k_time)))
            if len(kline_new) < 2:
                logging.debug('  ... No new records available ...')
                continue
            logging.debug('  ... %s new Records found', str(len(kline_new)))
            kline_new = kline_new.drop([6,7,8,9,10,11], axis = 1)
            kline_new = kline_new.apply(pd.to_numeric)
            kline_new.columns = ['open time', 'open', 'high', 'low', 'close', 'volume']
            kline_new['open time ux'] = kline_new['open time']

            logging.debug('  ... adding new klines to existing klines (if available)')
            klines = pd.concat([klines, kline_new], ignore_index=True)
            klines['open time'] = pd.to_datetime(klines['open time ux'], unit='ms')
            klines.sort_values(by=['open time ux'], inplace=True)

            
            if os.environ.get('USERNAME') == 'Jan':
                logging.debug('  ... adding technical indicators')
                #for indicator in indicators:
                #    if period is list:
                #        for period in klines_config[]
                #    else:
                #        klines[indicator + klines_config[indicator][period]] = TA.indicator(klines_config[indicator][period])
                klines['RSI'] = TA.RSI(klines, 14)
                klines['WilliamsR'] = TA.WILLIAMS(klines, 14)
                klines['WRSI'] = klines['RSI'] + klines['WilliamsR']
                #klines['EMA50'] = TA.EMA(klines, period=50)
                #klines['EMA100'] = TA.EMA(klines, period=100)
                #klines['EMA200'] = TA.EMA(klines, period=200)
                #klines['DEMA50'] = TA.DEMA(klines, period=50)
                #klines['DEMA100'] = TA.DEMA(klines, period=100)
                #klines['DEMA200'] = TA.DEMA(klines, period=200)

            logging.debug("  ... writing new records for " + str(pair))
            klines.to_csv(history_file_pair, index=False)
            logging.debug("  ... check API payload and wait for cool-off if necessary")
            hlp.API_weight_check(client)
            logging.info("--- FINISHED --- " + str(pair) + " --- " + interval + " --- " + str(paircount) + " / " + str(len(symbols)) + " ---")

    hlp.merge_klines(dir + '/1d/', dir, 'history_1d_klines_all_Assets.csv')

    logging.info("--- Finished --- binance kline downloading ---")
