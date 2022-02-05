Getting Started
===============

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
- The config file needs to be in the same folder from where you start the python script.

Starting Data Download
~~~~~~~~~~~~~~~~~~~~~~
- Change to a directory where you want to have the data being downloaded to and start the download of your data
  
  .. code:: bash

      python -m binance_reporting.start config.yaml

**For more information, feel free to browse through the next chapters.**

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