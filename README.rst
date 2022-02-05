===================================
Welcome to binance-reporting v0.2.0
===================================

Updated 05th Feb 2022

This is an **unofficial** Python downloader for `Binance exchange via its API <https://binance-docs.github.io/apidocs>`_. I am in no way affiliated with Binance. You can use it at your own risk.

If you came here looking for the `Binance exchange <https://www.binance.com/?ref=10099792>`_ to purchase cryptocurrencies, then `click here <https://accounts.binance.com/en/register?ref=CA3POK5P>`_.
If you are having an account at Binance already and want to download all your trading information from Binance, you ended up at the right place.

Source code
  https://github.com/JanAbraham/python-binance-reporting

Documentation
  https://python-binance-reporting.readthedocs.io/en/latest/

Many thanks goes to @sammchardy for providing the python-binance package and keeps it up-to-date. I am using this package to connect seemless to the exchange.

Features
--------
Downloading of your data from Binance for 
  - current balance
  - trading history
  - order history
  - open orders
  - deposit history
  - withdrawal history
  - daily account snapshots
  - sending a short telegram message with the balance & profit of your account

In addition to your own data, you can download general available data as well
  - prices of all trading pairs
  - kline history

One common issue when downloading data are API overloads. When that happens the data stream will just stop and the other side will close the connection. This is being taken care of and cool-off times have been implemented as appropriate.

Depending on your trading history with Binance, the first download might take some time to complete. Even more when you add kline downloads for many trading pairs and intervals. You can always watch the status of the download either on the console or in the log-file.
Every download attempt is first checking for previous data downloads and only performs a differential download.

Quick Start
-----------

Pre-Requisites
~~~~~~~~~~~~~~
- Register an account with `Binance <https://accounts.binance.com/en/register?ref=CA3POK5P>`_.
- Generate an `API Key <https://www.binance.com/en/my/settings/api-management>`_ and assign relevant permissions.

Installation
~~~~~~~~~~~~
- The package can be installed via pip from PYPI.org

  .. code:: bash

      pip install binance-reporting
    
Configuration
~~~~~~~~~~~~~
- The script is controlled by a yaml config file. You can download a `Template of a config file <https://github.com/JanAbraham/binance-reporting/blob/main/configs/config_template.yaml>`_
- Detailed information about how to use the configuration file is in the template and in this `chapter <https://binance-reporting.readthedocs.io/en/latest/config.html>`_.
- The config file need to be in the same folder from where you start the python script.

Starting Data Download
~~~~~~~~~~~~~~~~~~~~~~
- Change to a directory where you want to have the data being downloaded to and start the download of your data
  
  .. code:: bash

      python -m binance_reporting.start config.yaml



For more information, please `check out the documentation <https://binance-reporting.readthedocs.io/en/latest/>`_.

Contribute
----------
If you like to contribute or have an idea for improvements / enhancements, please contact me via github https://github.com/JanAbraham
  
  - `Source Code <https://github.com/JanAbraham/binance-reporting>`_

Please be informed, that I am only working sporadically on this project. I apologize already for longer response times.


Support
-------
If you are having issues, please open an item here:
  - `Issue Tracker <https://github.com/JanAbraham/binance-reporting/issues>`_

Donate
------
If this library helped you out, feel free to donate.

- XRP: rEb8TK3gBgk5auZkwc6sHnwrGVJH8DuaLh / MEMO: 101430969 (Ripple Network)
- TRX: TH14B1PT6bPfz2RF5C1hiP2G62438v113r (TRON / TRX20 Network)
- BTC, ETH, BNB, ADA, USDT, USDC: 0x4c2c124cf608f6002606c43287915937dae02c50  (Binance Smart Chain / BEP20 Network)

License
-------
The project is licensed under GNU General Public License.