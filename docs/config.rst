.. _configuration:
Configuration
=============

- The binance downloader can (and must) be customized by a config file.
- In general, the downloads are saved in csv files. These are stored in sub-directory from where the script has been started. The configuration file needs to be located in this very same directory as well.
- You can as well create different configuration files for a sub-set of the modules. This is often used when there are scheduled tasks, e.g. a daily task for downloading kline history and an hourly task for downloading account balances.

A minimum configuration file must have the sections *modules* and *accounts*.

Minimum Configuration
=====================

Modules
-------
The binance-reporting library has plenty of modules, which can be executed separately or all together in one run.

Following modules are currently available:

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
This section is critical for downloading account specific information from the exchange. Most important are the PUBLIC & SECRET to make a connection to the exchange.

.. note::Please ensure that your API keys only have read access. No trading or transfer permissions are needed.

This library requires you to save the API keys as environment variables in your local environment. Please dont provide the API keys themselves, but only add the names of the environment variables into the config file.

.. code-block:: yaml

    # provide account details to access binance
    # the below entries is only an example and need to be changed with your own data
    accounts:
        # provide a name for your account
        <name1>:
            # the following 4 values are mandatory
            # name of a sub-directory where the csv files related to this account are saved
            # it is a sub-directory from where this script is run
            # in case you run this via scheduler, make sure you change to the right directory
            dir: <dir-name-1>
            # type of account: SPOT or FUTURES
            type: SPOT or FUTURES
            # PUBLIC/SECRET key combination for accessing the API of the exchange and pulling your information
            # the actual key needs to be stored as an environment variable on your local machine
            # the name of the environment variable is given below
            osvar_api_public: <env variable for PUBLIC key account1>
            osvar_api_secret: <env variable for SECRET key account1>
            # following parameters are optional and only needed when activating the ticker module
            chat_pseudo: <chat-pseudo> # provide any text, which is used to identify the different msg on telegram
            chat_id: '@<chat-id of your telegram channel>'
            # following values are for calculating the PnL of your account in the telegram ticker message
            investment: 0
            cash: 0
            # portval = overall value of the porfolio; this is used as a basis to calculate the profit
            portval: 0
            profit: 0
        <name2>:
            dir: <dir-name-2>
            type: SPOT or FUTURES
            osvar_api_public: <env variable for PUBLIC key account2>
            osvar_api_secret: <env variable for SECRET key account2>
            chat_pseudo: <chat-pseudo>
            chat_id: '@<chat-id of your telegram channel>'
            investment: 0
            cash: 0
            portval: 0
            profit: 0

Extented Configuration
======================

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

Telegram ticker
---------------
You can send a short message to a pubic telegram channel. To do this, following information is needed in the configuration file. To ensure proper calculation of values, you need to provide the values in the accounts module.

.. code-block:: yaml

    # in case the module 'ticker' is set to 'yes', this section is needed to configure telegram
    telegram:
        # used for pushing notifications to Telegram
        # make sure the provided token has access to the telegram channel you want to send the message to
        # the telegram channel needs to be public
        token: <token>

    # in case the module 'ticker' is set to 'yes', this section can be used to bundle different accounts
    # and send a summary of these accounts to a telegram channel
    # the below entries are only an example and need to be changed with your own data
    account_groups:
        # multiple account groups can be defined
        ALL:
            # list all the accounts which are part of this group
            accounts: [<name1>, <name2>]
            chat_id: '@<chat-id of your telegram channel>'
            chat_pseudo: all
        SPOT:
            accounts: [<name1>]
            chat_id: '@<chat-id of your telegram channel>'
            chat_pseudo: spot-all
        FUT:
            accounts: [<name2>]
            chat_id: '@<chat-id of your telegram channel>'
            chat_pseudo: fut-all
        HODL:
            accounts: [<name1>]
            chat_id: '@<chat-id of your telegram channel>'
            chat_pseudo: hodl-all

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