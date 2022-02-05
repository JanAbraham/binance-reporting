Getting Started
===============

Pre-Requisites
--------------
- Register an account with `Binance <https://accounts.binance.com/en/register?ref=CA3POK5P>`_.
- Generate an `API Key <https://www.binance.com/en/my/settings/api-management>`_ and assign relevant permissions.

Installation
------------
- The package can be installed via pip from PYPI.org

  .. code:: bash

      pip install binance-reporting
    
Configuration
-------------
- The script is controlled by a yaml config file. You can download a `Template of a config file <https://github.com/JanAbraham/binance-reporting/blob/main/configs/config_template.yaml>`_
- Detailed information about how to use the configuration file is in the template and in this `chapter <https://binance-reporting.readthedocs.io/en/latest/config.html>`_.
- The config file needs to be in the same folder from where you start the python script.

Starting Data Download
----------------------
- Change to a directory where you want to have the data being downloaded to and start the download of your data
  
  .. code:: bash

      python -m binance_reporting.start config.yaml

**For more information, feel free to browse through the next chapters.**