.. _configuration:
Configuration
=============

- The binance downloader can (and must) be customized by a config file.
- In general, the downloads are saved in csv files. These are stored in sub-directory from where the script has been started. The configuration file needs to be located in this very same directory as well.
- You can as well create different configuration files for a sub-set of the modules. This is often used when there are scheduled tasks, e.g. a daily task for downloading kline history and an hourly task for downloading account balances.

Modules
-------
The binance-reporting library has plenty of modules, which can be executed separately. 

Following modules can be activated:

.. code-block:: yaml

    # defining the modules to be run
    # 'yes' means this module will run, 'no' means it wont
    # instead of 'no', you can as well remove the line
    modules:
        # downloading balances and creating a csv file with the details
        balances: yes
        # downloading daily snapshots. one line per day and saved in an csv file
        daily_account_snapshots: no
        # history of trades on the provided account(s)
        trades: no
        # history of orders on the provided account(s)  
        orders: no
        # currently open orders
        open_orders: no
        # history of deposits on the provided account(s)
        deposits: no
        # history of withdrawals on the provided account(s)
        withdrawals: no
        # downloading balances and sending a msg to a telegram channel
        # to use this, a separate section 'telegram' is expected (see below)
        ticker: no
        # downloads current prices of all assets traded on the exchange and saves it into a csv
        prices: no
        # if klines is 'yes', a separate section 'klines' is expected 'see below'
        klines: no

Accounts
--------
For which accounts should the data be downloaded for?

Klines
------
There is a module to download history information from the exchange.

.. code-block:: yaml
    
    # in case the module 'kline' is set to 'yes', this section is needed to configure kline downloads
    klines:
        # name of directory, in which the klines data should be stored
        # this is a sub-directory of the location from where the python script has been started
        dir: klines_data
        # list of intervals, for which klines should be downloaded
        # can be multiple entries
        intervals: ['5m', '1d']
        # list of symbols, for which klines should be downloaded
        # if empty, all the tradingpairs will be taken from the exchange
        # you can also only provide a text, which needs to be included 
        # in the trading symbol, e.g. 'USDT' would only take those 
        # trading pairs, which have USDT included, e.g. BTCUSDT, ADAUSDT etc
        # you can as well provide several items, like ['USDT', 'USDC', 'BTC']
        symbols: ['USDT']

Logging
-------
- Logging is done to the console, but ca be changed to file. This comes especially handy in case you start the data download as a scheduled task.
- Only INFO messages are shown. However, this can be customized as shown below

.. code-block:: yaml

    logging:
        # used for writing status messages
        # activate logging or not: yes/no
        log_activate: yes
        # log levels could be: DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_level: INFO
        # log target can be set to file or console
        log_target: console
        # in case log_target is set to file, this filename will be used
        # and stored in the folder from where this script is running
        log_file : binance-reporting.log