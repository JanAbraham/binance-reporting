==========================================
Welcome to python-binance-reporting v0.1.0
==========================================

Updated 28th Jan 2022

This is an **unofficial** Python downloader for `Binance exchange REST API v3 <https://binance-docs.github.io/apidocs/spot/en>`_. I am in no way affiliated with Binance. You can use it at your own risk.

If you came here looking for the `Binance exchange <https://www.binance.com/?ref=10099792>`_ to purchase cryptocurrencies, then `click here <https://accounts.binance.com/en/register?ref=CA3POK5P>`_.
If you are having an account at Binance already and want to download all your trading information from Binance, you might find something useful below.

Source code
  https://github.com/JanAbraham/python-binance-reporting

Documentation
  https://python-binance-reporting.readthedocs.io/en/latest/

Many thanks goes to SamyMcChardy for providing the python-binance package and keeps it up-to-date. I am using this package to connect seemless to the exchange.

Features
--------

Downloading of your data from Binance for 
  - trading history
  - order history
  - open orders
  - deposit history
  - withdrawal history
  - daily account snapshots for the last 180 days (limited to 180 days by Binance)
  - ad-hoc balance download

One common issue when downloading the data are api payloads. This is being taken care of.
Depending on your trading history with Binance, the first download might take some time to complete.
Every following download is first checking for any previous data downloads and only performs a differential download.

Quick Start
-----------

`Register an account with Binance <https://accounts.binance.com/en/register?ref=CA3POK5P>`_.

`Generate an API Key <https://www.binance.com/en/my/settings/api-management>`_ and assign relevant permissions.

.. code:: bash

    pip install python-binance-reporting


For more `check out the documentation <https://python-binance-reporting.readthedocs.io/en/latest/>`_.

Donate
------

If this library helped you out, feel free to donate.

BTC, ETH, BNB, ADA, USDT, USDC:
  - Binance Smart Chain / BEP20 Network: 0x4c2c124cf608f6002606c43287915937dae02c50
XRP:
  - Ripple Network: rEb8TK3gBgk5auZkwc6sHnwrGVJH8DuaLh / MEMO: 101430969
TRX:
  - TRON / TRX20 Network: TH14B1PT6bPfz2RF5C1hiP2G62438v113r

Contribute
----------

If you like to contribute or have an idea for improvements / enhancements, please contact me via github https://github.com/JanAbraham
  
  - Source Code: https://github.com/JanAbraham/python-binance-reporting

Please be informed, that I am only working sporadically on this project. I apologize already for longer response times.

Support
-------

If you are having issues, please open an item here:
  - Issue Tracker: https://github.com/JanAbraham/python-binance-reporting/issues

License
-------

The project is licensed under GNU General Public License.