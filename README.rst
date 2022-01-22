========================================
Welcome to python-binance-reporting v0.1
========================================

Updated 22nd Jan 2022

This is an unofficial Python downloader for `Binance exchange REST API v3 <https://binance-docs.github.io/apidocs/spot/en>`_. I am in no way affiliated with Binance, use at your own risk.

If you came here looking for the `Binance exchange <https://www.binance.com/?ref=10099792>`_ to purchase cryptocurrencies, then `go here <https://www.binance.com/?ref=10099792>`_.
If you are having an account at Binance already and want to download all your trading information from Binance, you might find something useful below.

Source code
  https://github.com/JanAbraham/python-binance-reporting

Documentation
  https://python-binance-reporting.readthedocs.io/en/latest/

Features
--------

Downloading of your data from Binance for 
  - trading history
  - order history
  - open orders
  - daily account snapshots for the last 180 days (limited to 180 days by Binance)
  - withdrawal history
  - deposit history
  - ad-hoc balance download

One common issue when downloading the data are api payloads. This is being taken care of.
Depending on your trading history with Binance, the first download might take some time to complete.
Every following download is first checking for any existing data and only performs a differential download.

Quick Start
-----------

`Register an account with Binance <https://accounts.binance.com/en/register?ref=10099792>`_.

`Generate an API Key <https://www.binance.com/en/my/settings/api-management>`_ and assign relevant permissions.


.. code:: bash

    pip install python-binance-reporting


For more `check out the documentation <https://python-binance.readthedocs.io/en/latest/>`_.

Donate
------

If this library helped you out feel free to donate.

- XRP:
- ETH: 
- BTC: 