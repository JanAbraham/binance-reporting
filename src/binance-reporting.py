"""Different functions for downloading and saving data from exchange.

functions available for:
    - history of trades
    - history of orders
    - open orders
    - deposits
    - withdrawals
    - daily snapshots

if it is called directly, it will download all mentioned above
TODO re-work withdrawals equal to deposits
TODO remove all df.empty queries
TODO add docstrings to each function
TODO add configuration file
TODO add funtion to merge info of different accounts into one file for 
        better reporting with excel pivot tables
TODO standardize column names accross different files
        (e.g. insertTime vs. updateTime vs. updatetime or 
        asset vs. coin)
TODO add an addresslist-translation-file to translate cryptic address names into 
        human readable names and use it for deposits & withdrawals
"""
import os  # set home directory of current user depending on OS
import time
import logging
import pandas as pd
from binance.client import Client

logfile = "binance-reporting.log"
loglevel = "INFO"  #'INFO', 'DEBUG'
logging.basicConfig(
    level=loglevel,
    filename=logfile,
    format="%(asctime)s:%(levelname)s:%(module)s:%(lineno)d:\
    %(funcName)s:%(message)s",
)


def download_balances(
    account_name: str,  # used to differentiate info in debug log
    account_type: str,
    PUBLIC: str,
    SECRET: str,
    balances_file: str,  # should include complete path
    bal_fut_positions_file: str,
    bal_fut_assets_file: str,
    writetype: str,  # 'a' or 'w'
    ):
    """download balances from exchange and write it into a csv file

    Arguments:
    - account_name -- Is used in the log file for easier debugging.
    - PUBLIC -- public part of API key to open connection to exchange
    - SECRET -- secret part of API key to open connection to exchange
    - balances_file -- name and location of the csv file
        to be filled with balances info
    - bal_fut_positions_file -- name and location of the csv file
        to be filled with future positions info
    - bal_fut_assets_file -- name and location of the csv file
        to be filled with futures assets info
    - writetype -- indicates if balances should be added ('a')
        or a new file should be written ('w')
    Returns:
    - writes csv file with balances of the binance account
    - the USD value of free & locked assets, cash available
        and the overall portfolio value
    TODO add 'account_name' and 'account_type' into csv files
    TODO downloading balances of future accounts
    """
    logging.info("Start downloading balances for Account: " + account_name)
    logging.debug("connecting to binance ...")

    client = Client(api_key=PUBLIC, api_secret=SECRET)

    logging.debug("reading balances and prices from exchnge ...")
    API_weight_check(client)
    fut_pos = pd.DataFrame()
    fut_assets = pd.DataFrame()
    prices = pd.DataFrame(client.get_all_tickers())
    if account_type == "FUTURES":
        balances = pd.DataFrame()
        logging.debug('reading values for portval')
        accountinfo_fut = client.futures_account()
        API_close_connection(client)
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
            'NetValue' : float(accountinfo_fut['totalWalletBalance']) + float(accountinfo_fut['totalUnrealizedProfit']),
            'UTCtime' : pd.to_datetime("now")
        }
        balances = balances.append(portval, ignore_index=True)
        balances['Account'] = account_name
        balances['Acccount type'] = account_type
    
        logging.debug("collecting future account positions and assets")
        fut_pos = pd.DataFrame(accountinfo_fut['positions'])
        fut_pos.drop(fut_pos[fut_pos.initialMargin == '0'].index, inplace = True)
        fut_pos['USDT price'] = 0
        for symbol in fut_pos["symbol"]:
            fut_pos["USDT price"].loc[fut_pos.symbol == symbol] = (prices["price"].loc[prices.symbol == symbol].iloc[0])
            fut_pos['UTCtime'] = pd.to_datetime(fut_pos["updateTime"], unit='ms')
        fut_pos['Account'] = account_name
        fut_pos['Acccount type'] = account_type
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
            "asset": "PortVal",
            "Asset value": fut_assets["Asset value"].sum(),
        }
        fut_assets = fut_assets.append(portval, ignore_index=True)

        fut_assets['UTCtime'] = pd.to_datetime("now")
        fut_assets['Account'] = account_name
        fut_assets['Acccount type'] = account_type

        logging.debug("collect return values of function")
        result = {
            "updatetime": pd.to_datetime("now"),
            'maintmargin' : float(accountinfo_fut['totalMaintMargin']), #needed for Ticker => check if we are close to Liquidation
            'walletbalance' : float(accountinfo_fut['totalWalletBalance']), #needed for Ticker => Brutto Value
            'pnl' : float(accountinfo_fut['totalUnrealizedProfit']), #needed for Ticker => PnL
            'cash' : float(accountinfo_fut['totalMarginBalance']) - float(accountinfo_fut['totalMaintMargin']), #needed for Ticker => Balance
            "portval": float(balances["NetValue"].values[0])
        }
        logging.info("Finished downloading balances for " + account_type + "-Account of " + account_name)
        fut_pos.to_csv(bal_fut_positions_file, index=False)
        fut_assets.to_csv(bal_fut_assets_file, index=False)


    if account_type == 'SPOT':
        accountinfo = client.get_account()
        API_close_connection(client)
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
            "asset": "PortVal",
            "Free Coin Value": balances["Free Coin Value"].sum() - free_coin_value,
            "Locked Coin Value": balances["Locked Coin Value"].sum(),
            "Asset value": balances["Asset value"].sum(),
        }
        balances = balances.append(portval, ignore_index=True)
        balances["update time"] = pd.to_datetime("now")

        logging.debug("collect return values of function")
        result = {
            "updatetime": pd.to_datetime("now"),
            "free_coin_value": portval["Free Coin Value"],
            "locked_coin": portval["Locked Coin Value"],
            "cash": free_coin_value,
            "portval": portval["Asset value"],
        }

    logging.debug("write balances to " + balances_file)
    if writetype == "a":
        balances.to_csv(balances_file, index=False, header=False, mode=writetype)
    else:
        balances.to_csv(balances_file, index=False)

    logging.info("Finished downloading balances for " + account_type + "-Account of " + account_name)

    return result


def download_daily_account_snapshots(
    account_name,
    account_type,
    PUBLIC,
    SECRET,
    snapshots_balances_file,
    snapshots_positions_file,
    snapshots_assets_file
    ):
    """download daily account snapshots from exchange and write it into a csv file

    In order to reduce load on the API, the function verifies if a csv-
    file already exists. If so, it reads it to determine the time of the last
    downloaded snapshot. If you want to re-download all snapshots again, you
    just need to delete this file. Be cautious: Binance only holds max.
    180 days of snapshots. In case you want to go back furhter, these
    days might be your only available information about older snapshots
    written by this procedure in case you have run it before.

    For every balances snapshot, the asset value from the day of the snapshot
    is being downloaded ('close' value of the daily kline from the snapshot
    day). Sometimes the kline value is not available anymore, where '0' value
    is being filled in.

    Arguments:
    - account_name -- Is used in the log file for easier debugging.
    - account_type -- either SPOT or FUTURES
    - PUBLIC -- public part of API key to open connection to exchange
    - SECRET -- secret part of API key to open connection to exchange
    - values_file -- csv file for overall daily portfolio values
    - balances_file -- csv file for detailed balances per asset per day

    Returns:
    - writes csv file with snapshots of the binance account
    TODO add snapshot download of Futures Account
    """
    import math

    logging.info(
        "Start downloading daily snapshots for "
        + account_type
        + "-Account of "
        + account_name
    )

    # customizable variables
    snapshot_days_max = 180  # Binance only saves snapshots only for last 180 days
    snapshot_days_per_request = 30  # amount of snapshot days per request to exchange

    # internal variables
    daily_ms = 86400000  # = milliseconds per day
    step_ms = daily_ms * snapshot_days_per_request
    snapshot_days_max_ms = snapshot_days_max * daily_ms
    current_time_ms = math.trunc(time.time() * 1000)  # current time in milliseconds

    #if account_type == "FUTURES":
    #    result = "Sorry, future accounts are not yet supported by this procedure."
    #    return result

    logging.debug(
        "verify if csv file already exists and \
        determine last recorded snapshot"
    )
    balances = pd.DataFrame()
    start_time_ms = current_time_ms - snapshot_days_max_ms
    if os.path.isfile(snapshots_balances_file):
        balances = pd.read_csv(snapshots_balances_file)
        start_time_ms = balances["updateTime"].max() + 1

    if current_time_ms - start_time_ms < daily_ms:
        logging.info("No newer snapshot available.")
        logging.debug("Date of last recorded snapshot is " + str(pd.to_datetime(start_time_ms, unit="ms")))
        return

    logging.debug("Opening connection to exchange ...")
    client = Client(api_key=PUBLIC, api_secret=SECRET)
    client.REQUEST_TIMEOUT = (
        30  # default value of 10 is too low for 30 days snapshot download per request
    )
    snapshots = pd.DataFrame()
    logging.debug("download " + account_type + " snapshots for Account " + account_name)
    while start_time_ms < current_time_ms:
        logging.info(
            "timeframe of snapshot download: "
            + str(pd.to_datetime(start_time_ms, unit="ms"))
            + " to "
            + str(pd.to_datetime(start_time_ms + step_ms, unit='ms'))
        )
        API_weight_check(client)
        try:
            new_snapshot = pd.DataFrame(client.get_account_snapshot(
                    type=account_type,
                    startTime=int(start_time_ms),
                    endTime=int(start_time_ms + step_ms))
            )
        except:
            logging.warning("API error. Trying again")
            continue
        snapshots = snapshots.append(new_snapshot, ignore_index=True)
        start_time_ms = start_time_ms + step_ms + 1

    API_close_connection(client)

    logging.debug("writing snapshots to csv ...")

    if account_type == "SPOT":
        for snapshot in snapshots["snapshotVos"]:
            updatetime_ms = snapshot["updateTime"]
            updatetime_utc = pd.to_datetime(snapshot["updateTime"], unit="ms")
            # adding some additional data to daily balances:
            #   - updatetime
            #   - USDT Price per asset from the date of the snapshot
            #   - PortVal = Value of all balances together from this day
            balance = pd.DataFrame(snapshot["data"]["balances"])
            balance[["free", "locked"]] = balance[["free", "locked"]].apply(
                pd.to_numeric
            )
            balance.drop(
                balance[(balance.free == 0) & (balance.locked == 0)].index, inplace=True
            )
            prices = pd.DataFrame(
                client.get_all_tickers()
            )  # get list of tickers and prices
            prices["price"] = pd.to_numeric(prices["price"])
            logging.info(
                "add USDT prices to assets from snapshot of " + str(updatetime_utc)
            )
            balance["USDT symbol"] = balance["asset"] + "USDT"
            balance["USDT price"] = 0
            symbol_shortlist = prices[prices["symbol"].isin(balance["asset"] + "USDT")]
            for symbol in symbol_shortlist["symbol"]:
                kline = pd.DataFrame(
                    client.get_historical_klines(
                        symbol,
                        Client.KLINE_INTERVAL_1DAY,
                        updatetime_ms,
                        updatetime_ms + daily_ms,
                    )
                )
                logging.debug(
                    "downloading historic prices for "
                    + symbol
                    + ". API payload: "
                    + str(API_weight_check(client))
                )
                if not kline.empty:
                    balance["USDT price"].loc[balance["USDT symbol"] == symbol] = float(
                        kline[4][0]
                    )
                else:
                    balance["USDT price"].loc[balance["USDT symbol"] == symbol] = 0
            balance.drop("USDT symbol", inplace=True, axis=1)
            balance["USDT price"].loc[balance.asset == "USDT"] = 1
            logging.debug("calculate additional values for the balance overview")
            balance["Free Coin Value"] = balance["free"] * balance["USDT price"]
            balance["Locked Coin Value"] = balance["locked"] * balance["USDT price"]
            balance["Asset value"] = (
                balance["Free Coin Value"] + balance["Locked Coin Value"]
            )
            balance.sort_values(by=["asset"], inplace=True)
            if balance.loc[balance["asset"] == "USDT"].empty:
                free_coin_value = 0
            else:
                free_coin_value = balance["Free Coin Value"].loc[balance["asset"] == "USDT"].iloc[0]
            portval = {
                "asset": "PortVal",
                "Free Coin Value": balance["Free Coin Value"].sum()- free_coin_value,
                "Locked Coin Value": balance["Locked Coin Value"].sum(),
                "Asset value": balance["Asset value"].sum(),
            }
            balance = balance.append(portval, ignore_index=True)
            balance["updateTime"] = updatetime_ms
            balance["UTCTime"] = updatetime_utc
            balance["account"] = account_name
            balance["type"] = account_type
            balances = balances.append(balance, ignore_index=True)
            # to mitigate potential timeout errors during long running
            # scripts, data is written after every new record
            # 
            # several date formatting actions to ensure
            # - UTCTime does not contain hh:mm:ss (for better handling in excel)
            # - no duplicates
            # - 'UTCTime' cannot be sorted unfortunately, but 'updateTime' can still be
            #
            balances['UTCTime'] = pd.to_datetime(balances['UTCTime'])
            balances['UTCTime'] = pd.to_datetime(balances['UTCTime']).dt.date
            balances['UTCTime'] = pd.to_datetime(balances['UTCTime'])
            balances['UTCTime'] = pd.to_datetime(balances['UTCTime'], format="%d/%m/%Y")
            balances.drop_duplicates(
                    subset=["UTCTime", "asset", "account", "type"], keep="last", inplace=True
                    )
            balances.to_csv(snapshots_assets_file, index=False, date_format="%d/%m/%Y")

        balances = balances.loc[balances.asset == "PortVal"]
        balances.drop(['free', 'locked', 'USDT price'], axis=1, inplace=True)

    if account_type == "FUTURES":
        fut_balances_new = pd.DataFrame()
        fut_assets_new = pd.DataFrame()
        fut_pos_new = pd.DataFrame()
        fut_pos_hist = pd.DataFrame()
        fut_assets_hist = pd.DataFrame()
        kline = pd.DataFrame()

        # determine previous downloads, if available
        if os.path.isfile(snapshots_positions_file):
            fut_pos_hist = pd.read_csv(snapshots_positions_file)
        if os.path.isfile(snapshots_assets_file):
            fut_assets_hist = pd.read_csv(snapshots_assets_file)

        for snapshot in snapshots["snapshotVos"]:
            updatetime_ms = snapshot["updateTime"]
            updatetime_utc = pd.to_datetime(snapshot["updateTime"], unit="ms")

            assets = pd.DataFrame(snapshot["data"]["assets"])
            assets['USDT price'] = 0
            for asset in assets['asset']:
                if asset == 'USDT':
                    price = 1
                else:
                    logging.info(
                        "downloading historic prices for "
                        + asset
                        + ". API payload: "
                        + str(API_weight_check(client))
                    )
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
                assets["USDT price"].loc[assets["asset"] == asset] = price
                
            positions = pd.DataFrame(snapshot["data"]["position"])
            positions["updateTime"] = updatetime_ms
            fut_pos_new = fut_pos_new.append(positions, ignore_index=True)

            assets["updateTime"] = updatetime_ms
            assets[["marginBalance", "walletBalance", "USDT price"]] = assets[["marginBalance", "walletBalance", "USDT price"]].apply(pd.to_numeric)
            assets['Margin value'] = assets['marginBalance'] * assets['USDT price']
            assets['Wallet value'] = assets['walletBalance'] * assets['USDT price']
            assets['PnL'] = assets['marginBalance'] - assets['walletBalance']
            assets["Asset value"] = 0
            portval_asset = {
                "asset": "PortVal",
                "Margin value": assets["Margin value"].sum(),
                "Wallet value": assets["Wallet value"].sum(),
                "PnL" : assets["PnL"].sum(),
                "updateTime": updatetime_ms,
                "Asset value": assets["Margin value"].sum()
            }
            assets = assets.append(portval_asset, ignore_index=True)
            fut_assets_new = fut_assets_new.append(assets, ignore_index=True)

        fut_assets_new["UTCTime"] = pd.to_datetime(fut_assets_new["updateTime"], unit="ms")
        fut_assets_new["account"] = account_name
        fut_assets_new["type"] = account_type

        fut_assets_hist = fut_assets_hist.append(fut_assets_new, ignore_index=True)
        # 
        # several date formatting actions to ensure
        # - UTCTime does not contain hh:mm:ss (for better handling in excel)
        # - no duplicates
        # - 'UTCTime' cannot be sorted unfortunately, but 'updateTime' can still be
        #
        fut_assets_hist['UTCTime'] = pd.to_datetime(fut_assets_hist['UTCTime'])
        fut_assets_hist['UTCTime'] = pd.to_datetime(fut_assets_hist['UTCTime']).dt.date
        fut_assets_hist['UTCTime'] = pd.to_datetime(fut_assets_hist['UTCTime'])
        fut_assets_hist['UTCTime'] = pd.to_datetime(fut_assets_hist['UTCTime'], format="%d/%m/%Y")
        fut_assets_hist.drop_duplicates(
                subset=["UTCTime", "asset", "account", "type"], keep="last", inplace=True
                )
        fut_assets_hist.to_csv(snapshots_assets_file, index=False, date_format="%d/%m/%Y")
        fut_pos_new[["entryPrice", "positionAmt", "unRealizedProfit"]] = fut_pos_new[
                ["entryPrice", "positionAmt", "unRealizedProfit"]
                ].apply(pd.to_numeric)
        fut_pos_new.drop(
            fut_pos_new[
                    (fut_pos_new.entryPrice == 0)
                    & (fut_pos_new.positionAmt == 0)
                    & (fut_pos_new.unRealizedProfit == 0)
                    ].index, inplace=True
                    )
        fut_pos_new['USDT price'] = fut_pos_new['markPrice']
        fut_pos_new["UTCTime"] = pd.to_datetime(fut_pos_new["updateTime"], unit="ms")
        fut_pos_new["account"] = account_name
        fut_pos_new["type"] = account_type
        fut_pos_hist = fut_pos_hist.append(fut_pos_new, ignore_index=True)
        fut_pos_hist.drop_duplicates(
                subset=["updateTime", "symbol"], keep="last", inplace=True
                )
        fut_pos_hist.to_csv(snapshots_positions_file, index=False, date_format="%d/%m/%Y")

        balances = fut_assets_hist[fut_assets_hist['asset'] == 'PortVal']
        balances.drop(['marginBalance', 'walletBalance', 'USDT price'], axis=1, inplace=True)
        
    # write daily portfolio balances
    balances.sort_values(by=['updateTime'], ascending=False, inplace=True)
    balances.to_csv(snapshots_balances_file, index=False, date_format="%d/%m/%Y")



    logging.info("Finished writing daily snapshots for account: " + account_name)


def download_trades(
    account_name, account_type, PUBLIC, SECRET, list_of_trading_pairs, trades_file
    ):
    #
    # get trades and write them to csv file
    #
    # verify if file already exists and determine last recorded trade

    if account_type == "FUTURES":
        result = "Sorry, future accounts are not yet supported by this procedure."
        return result
            
    trades = pd.DataFrame()
    last_rec_trade_time = 0
    if os.path.isfile(trades_file):
        trades = pd.read_csv(trades_file)

    new_trades = []

    logging.info("Start downloading trades for account: " + account_name)
    logging.debug("connecting to binance ...")

    # open connection to exchange
    client = Client(api_key=PUBLIC, api_secret=SECRET)

    for trading_pair in list_of_trading_pairs:
        logging.debug(
            "reading trades from Binance for Trading Pair " + trading_pair + "..."
        )
        API_weight_check(client)
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
            logging.debug(
                "  ... overall amount of not yet recorded trades read: "
                + str(len(new_trades))
            )
            logging.debug("  ... be gentle with the API and wait for 1sec")
            time.sleep(1)
        except Exception as e:
            logging.warning("Error: " + str(e.code) + " (" + e.message + ")")
            logging.warning(
                "Error with loading data for " + trading_pair + ". Trying next symbol."
            )

    logging.debug(
        "Amount of new Trading Records to be written: " + str(len(new_trades))
    )
    API_close_connection(client)

    # only write trades into csv file if there have been new trades found
    if not len(new_trades) == 0:
        # adding new trades to existing list of trades from csv
        trades = trades.append(new_trades, ignore_index=True)
        # add column with timestamp in a human readable format
        trades["UTCTime"] = pd.to_datetime(trades["time"], unit="ms")
        trades.sort_values(by=["time"], inplace=True, ascending=False)

        logging.debug("writing trades to csv ...")
        trades.to_csv(trades_file, index=False)

    logging.info(
        "Finished writing "
        + str(len(new_trades))
        + " Trades for account: "
        + account_name
    )


def download_orders(
    account_name, account_type, PUBLIC, SECRET, list_of_trading_pairs, orders_file
    ):

    logging.info("Start downloading orders for account: " + account_name)
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
        logging.debug(
            "reading orders from Binance for Trading Pair " + trading_pair + "..."
        )
        API_weight_check(client)
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
            logging.debug(
                "  ... overall amount of not yet recorded orders read: "
                + str(len(new_orders))
            )
            logging.debug("  ... be gentle with the API and wait for 1sec")
            time.sleep(1)
        except Exception as e:
            logging.warning("Error: " + str(e.code) + " (" + e.message + ")")
            logging.warning(
                "Error with loading data for " + trading_pair + ". Trying next symbol."
            )

    logging.debug("Amount of new Order Records to be written: " + str(len(new_orders)))
    API_close_connection(client)

    # only write orders into csv file if there have been new orders found
    if not len(new_orders) == 0:
        # adding new orders to existing list of orders from csv
        orders = orders.append(new_orders, ignore_index=True)
        # change format of timestamp to human readable format
        orders["UTCTime"] = pd.to_datetime(orders["time"], unit="ms")
        orders.sort_values(by=["time"], inplace=True, ascending=False)

        logging.debug("writing orders to csv ...")
        orders.to_csv(orders_file, index=False)
        logging.debug("Finished writing Orders!")

    logging.info(
        "Finished writing "
        + str(len(new_orders))
        + " orders for account: "
        + account_name
    )


def download_open_orders(account_name, account_type, PUBLIC, SECRET, open_orders_file):
    #
    # read open orders and write them into a csv file
    #

    logging.info("Start downloading open orders for account: " + account_name)
    logging.debug("connecting to binance ...")

    if account_type == "FUTURES":
        result = "Sorry, future accounts are not yet supported by this procedure."
        return result
        
    client = Client(api_key=PUBLIC, api_secret=SECRET)
    API_weight_check(client)

    logging.debug("reading all open orders from Binance ...")
    open_orders = pd.DataFrame(client.get_open_orders())
    if not open_orders.empty:
        logging.debug("change timestamps in the open orders to a readable format ...")
        # add column with timestamp in a human readable format
        open_orders["UTCTime"] = pd.to_datetime(open_orders["time"], unit="ms")
        # sorting open orders for time descending

    API_close_connection(client)
    logging.debug("writing open orders to csv ...")
    open_orders.to_csv(open_orders_file, index=False)
    logging.info("finished writing open orders to csv for account: " + account_name)


def download_deposits(account_name, account_type, PUBLIC, SECRET, deposits_file):
    """download account deposits from exchange and write it into a csv file

    In order to reduce load on the API, the function verifies if a csv-
    file already exists. If so, it reads it to determine the time of the last
    downloaded record. If you want to re-download all records again, you
    just need to delete this file. Be careful: a re-download of all records might
    take a while, depending on the amount of transactions you had.

    For every transaction, following data is being added to the downloadable
    data from the exchange:
        - USDT price of the asset (close price from the day of transaction)
        - overall value of coins in USDT from the day of the transaction
        - time of transaction in UTC format

    In case of the price of the coin is not available anymore,
    '0' value is being filled in.

    Arguments:
    - account_name -- Is used in the log file for easier debugging.
    - account_type -- either SPOT or FUTURES
    - PUBLIC -- public part of API key to open connection to exchange
    - SECRET -- secret part of API key to open connection to exchange
    - deposit_file -- csv file for all deposits

    Returns:
    - writes csv file with deposits of the binance account
    - returns dataframe with all deposits

    TODO add deposits for Futures Account
    """

    logging.info("Start downloading deposits for account: " + account_name)

    # customizable variables
    start_time_ms = 1498870800000  # 1.July 2021 GMT; binance exchange went online for public trading on 12.07.2017

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
        start_time_ms = int(deposits.insertTime.max() + 1)

    # fetch list of new deposits, if any
    logging.debug("connecting to binance ...")

    client = Client(api_key=PUBLIC, api_secret=SECRET)
    client.REQUEST_TIMEOUT = 10

    deposits_new = pd.DataFrame()
    while start_time_ms < current_time_ms:
        API_weight_check(client)
        deposits_new = deposits_new.append(
            pd.DataFrame(
                client.get_deposit_history(
                    startTime=start_time_ms, endTime=start_time_ms + step_ms
                )
            ),
            ignore_index=True,
        )
        start_time_ms = start_time_ms + step_ms + 1

    # work with downloaded deposits, if any
    if not deposits_new.empty:
        prices = pd.DataFrame(
            client.get_all_tickers()
        )  # get list of tickers and prices
        prices["price"] = pd.to_numeric(prices["price"])
        logging.info("add USDT prices to deposited assets")
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
                "downloading historic prices for "
                + symbol
                + ". API payload: "
                + str(API_weight_check(client))
            )
            kline = pd.DataFrame(
                client.get_historical_klines(
                    symbol, "1d", str(updatetime_ms), str(endtime_ms)
                )
            )
            deposits_new["USDT price"].loc[
                (deposits_new.insertTime == updatetime_ms)
                & (deposits_new["USDT symbol"] == symbol)
            ] = float(kline[4][0])
        API_close_connection(client)

        deposits_new.drop(["USDT symbol"], inplace=True, axis=1)
        deposits = deposits.append(deposits_new, ignore_index=True)
        logging.debug("calculate additional values for the deposits overview")
        deposits["USDT price"].loc[deposits.coin == "USDT"] = 1
        deposits[["amount", "USDT price", "Asset value"]] = deposits[
            ["amount", "USDT price", "Asset value"]
        ].apply(pd.to_numeric)
        deposits["Asset value"] = deposits["amount"] * deposits["USDT price"]
        deposits["UTCTime"] = pd.to_datetime(deposits["insertTime"], unit="ms")
        deposits.sort_values(by=["insertTime"], inplace=True)
        deposits.drop_duplicates(subset=["txId"], keep="last", inplace=True)

        logging.debug("writing deposits to csv ...")
        deposits.to_csv(deposits_file, index=False)

    logging.info("Finished writing deposits for account: " + account_name)
    return deposits


def download_withdrawals(account_name, account_type, PUBLIC, SECRET, withdrawals_file):
    """download account withdrawals from exchange and write it into a csv file

    In order to reduce load on the API, the function verifies if a csv-
    file already exists. If so, it reads it to determine the time of the last
    downloaded record. If you want to re-download all records again, you
    just need to delete this file. Be careful: a re-download of all records might
    take a while, depending on the amount of transactions you had.

    For every transaction, following data is being added to the downloadable
    data from the exchange:
        - USDT price of the asset (close price from the day of transaction)
        - overall value of coins in USDT from the day of the transaction
        - time of transaction in UTC format

    In case of the price of the coin is not available anymore,
    '0' value is being filled in.

    Arguments:
    - account_name -- Is used in the log file for easier debugging.
    - account_type -- either SPOT or FUTURES
    - PUBLIC -- public part of API key to open connection to exchange
    - SECRET -- secret part of API key to open connection to exchange
    - withdrawal_file -- csv file for all withdrawals

    Returns:
    - writes csv file with withdrawals of the binance account
    - returns dataframe with all withdrawals

    TODO add withdrawals for Futures Account
    """

    logging.info("Start downloading withdrawals for account: " + account_name)

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
        start_time_ms = int(transactions.insertTime.max() + 1)

    # fetch list of new transactions, if any
    logging.debug("connecting to binance ...")

    client = Client(api_key=PUBLIC, api_secret=SECRET)
    client.REQUEST_TIMEOUT = 10

    transactions_new = pd.DataFrame()
    while start_time_ms < current_time_ms:
        API_weight_check(client)
        transactions_new = transactions_new.append(
            pd.DataFrame(
                client.get_withdraw_history(
                    startTime=start_time_ms, endTime=start_time_ms + step_ms
                )
            ),
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
        logging.info("add USDT prices to deposited assets")
        transactions_new["USDT symbol"] = transactions_new["coin"] + "USDT"
        transactions_new[["USDT price", "Asset value"]] = 0.00
        transactions_new["insertTime"] = pd.to_datetime(transactions_new["applyTime"])
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
                "downloading historic prices for "
                + symbol
                + ". API payload: "
                + str(API_weight_check(client))
            )
            kline = pd.DataFrame(
                client.get_historical_klines(
                    symbol, "1d", str(updatetime_ms), str(endtime_ms)
                )
            )
            transactions_new["USDT price"][ind] = float(kline[4][0])
            # transactions_new['USDT price'].loc[(transactions_new.insertTime == updatetime_ms) & (transactions_new['USDT symbol'] == symbol)] = float(kline[4][0])
        API_close_connection(client)

        transactions_new.drop(["USDT symbol"], inplace=True, axis=1)
        transactions = transactions.append(transactions_new, ignore_index=True)
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
        ) * transactions["USDT price"]
        transactions["UTCTime"] = pd.to_datetime(transactions["insertTime"], unit="ms")
        transactions.sort_values(by=["insertTime"], inplace=True)
        transactions.drop_duplicates(subset=["id"], keep="last", inplace=True)

        logging.debug("writing transactions to csv ...")
        transactions.to_csv(withdrawals_file, index=False)

    logging.info("Finished writing withdrawals for account: " + account_name)
    return transactions


def download_prices(prices_file):
    #
    # read prices for all trading pairs and write them to prices.csv file
    #
    logging.info("Start downloading prices for all tradng pairs from exchange")
    logging.debug("connecting to binance ...")

    client = Client()

    logging.debug("reading all prices from Binance ...")
    prices = pd.DataFrame(client.get_all_tickers())
    logging.debug("writing prices to csv ...")
    prices.to_csv(prices_file, index=False)
    logging.info("Finished writing Prices!")


def API_weight_check(client):
    #
    # verify current payload of Binance API and trigger cool-off
    # if 85% of max payload has been reached
    # sends as well a keepalive signal for the api connection
    # Goal: avoid errors while downloading data from binance
    # Return: the payload value after checking & cool-off
    # TODO: read current max value for Payload from Binance config
    # TODO: SAPI API seems to have threshold of 12000 => incorporate those (discovered during snapshot downloads)
    import time  # used for sleep / cool-off

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
            logging.warning("Error: " + str(e.code) + " (" + e.message + ")")

    logging.debug(
        "Check payload of API finished. Current Payload is "
        + str(client.response.headers[api_header_used])
    )
    return client.response.headers[api_header_used]


def API_close_connection(client):
    #
    # close API connection of a given client
    # to keep the environment lean and clean
    # TODO add different connection types for futures etc.

    logging.debug("closing API connection")
    try:
        client.stream_close(client.stream_get_listen_key())
    except Exception as e:
        logging.warning("Error: " + str(e.code) + " (" + e.message + ")")
    logging.debug("API connection closed (if no error has been reported before)")


def file_remove_blanks(filename):
    #
    # read csv file and remove blank lines
    # those blank lines are sometimes created when saving
    # csv files under windows
    #
    logging.info("removing blank rows from " + filename)
    data = pd.read_csv(filename, skip_blank_lines=True, low_memory=False)
    data.dropna(how="all", inplace=True)
    data.to_csv(filename, header=True)
    logging.info("blank rows removed from " + filename)


def merge_files(sourcefiles: list, targetfile: str):
    data = pd.DataFrame()
    data_new = pd.DataFrame()
    for sourcefile in sourcefiles:
        if os.path.isfile(sourcefile):
            data_new = pd.read_csv(sourcefile)
            data = data.append(data_new, ignore_index=True)
    data.to_csv(targetfile, index=False)


def download_all():
    """downloading all account information from exchange

    this includes:
        - balances
        - history of trades
        - history of orders
        - open orders
        - deposits
        - withdrawals
        - daily snapshots
    """

    logging.info("Downloading all account information from Exchange")
    if os.name == "posix":
        home_dir = os.environ["HOME"]
    else:
        home_dir = os.environ["USERPROFILE"]

    current_time = time.strftime("%Y-%m-%d %H:%M:%S")

    logging.debug("get list of Trading Pairs to download data about ...")
    client = Client()

    # get all symbols from the exchange and sort them alphabetically
    trading_pairs_all = pd.DataFrame(client.get_all_tickers()).loc[:, ["symbol"]]
    trading_pairs_all.sort_values(by=["symbol"], inplace=True)

    # filter out USDT pairs
    # take this part out in case other trading pairs should be downloaded too
    list_of_trading_pairs = trading_pairs_all[
        trading_pairs_all.symbol.str.contains("USDT")
    ]
    list_of_trading_pairs = list_of_trading_pairs["symbol"].values.tolist()

    logging.debug(
        "Amount of Trading Pairs available on exchange: "
        + str(len(list_of_trading_pairs))
    )
    # get account specific information
    # defining variables

    account_names = ["JAN", "RITA", "JAKOB", 'JAN_COINS']
    account_types = ["SPOT", "FUTURES"]  # , 'FUTURES'] #'MARGIN'] # list of available types: https://binance-docs.github.io/apidocs/spot/en/#daily-account-snapshot-user_data

    logging.info("looping through accounts and account types")
    # merge snapshot files for reporting with excel pivot tables
    for account_name in account_names:
        for account_type in account_types:
            if (account_name == 'JAKOB' or account_name == 'JAN_COINS') and account_type == 'FUTURES':
                continue
            PUBLIC = os.environ.get("READ_PUBLIC_" + account_name + "_" + account_type)
            SECRET = os.environ.get("READ_SECRET_" + account_name + "_" + account_type)

            file_directory = (
                home_dir + "/dropbox/finance/binance/source data/" + account_name + "/"
            )
            open_orders_file = file_directory + "open_orders_" + account_name + ".csv"
            orders_file = file_directory + "orders_" + account_name + ".csv"
            trades_file = file_directory + "trades_" + account_name + ".csv"
            balances_file = file_directory + "balances_" + account_name + "_" + account_type + ".csv"
            bal_fut_positions_file = file_directory + "balances_" + account_name + "_" + account_type + "_positions.csv"
            bal_fut_assets_file = file_directory + "balances_" + account_name + "_" + account_type + "_assets.csv"
            prices_file = file_directory + "prices_" + account_name + ".csv"
            deposits_file = file_directory + "deposits_" + account_name + ".csv"
            withdrawals_file = file_directory + "withdrawals_" + account_name + ".csv"
            snapshots_balances_file = (file_directory + "snapshot_daily_" + account_name + "_" + account_type + "_balances.csv")
            snapshots_assets_file = (file_directory + "snapshot_daily_" + account_name + "_" + account_type + "_assets.csv")
            snapshots_positions_file = (file_directory + "snapshot_daily_" + account_name + "_" + account_type + "_positions.csv")

            writetype = "w"
    
            download_balances(
                account_name, account_type, PUBLIC, SECRET, balances_file, bal_fut_positions_file, bal_fut_assets_file, writetype
            )
            
            download_trades(
                account_name,
                account_type,
                PUBLIC,
                SECRET,
                list_of_trading_pairs,
                trades_file,
            )

            download_orders(
                account_name,
                account_type,
                PUBLIC,
                SECRET,
                list_of_trading_pairs,
                orders_file,
            )

            download_open_orders(
                account_name, account_type, PUBLIC, SECRET, open_orders_file
            )

            download_deposits(account_name, account_type, PUBLIC, SECRET, deposits_file)

            download_withdrawals(
                account_name, account_type, PUBLIC, SECRET, withdrawals_file
            )

            download_daily_account_snapshots(
                account_name,
                account_type,
                PUBLIC,
                SECRET,
                snapshots_balances_file,
                snapshots_positions_file,
                snapshots_assets_file
            )

            download_prices(prices_file)

            logging.info(
                "Finished downloading and writing all account data from Binance for "
                + account_type
                + "-account of "
                + account_name
            )

    logging.info("Merging snapshot files from different accounts!")            
    targetfile = (home_dir + "/dropbox/finance/binance/source data/snapshots_daily_all_accounts.csv")
    sourcefiles = []
    account_names = ['JAN', 'RITA', 'JAKOB', 'JAN_COINS']
    account_types = ['SPOT', 'FUTURES']
    for account_type in account_types:
        for account_name in account_names:
            file_directory = home_dir + "/dropbox/finance/binance/source data/" + account_name + "/"
            filename = (
                file_directory
                + "snapshot_daily_"
                + account_name
                + "_"
                + account_type
                + "_balances"
                + ".csv"
            )
            sourcefiles.append(filename)
    merge_files(sourcefiles, targetfile)
    logging.info("Merging snapshot files finished!")

if __name__ == "__main__":
    download_all()
