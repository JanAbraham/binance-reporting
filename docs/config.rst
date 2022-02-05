.. _configuration:
Configuration
=============

The binance downloader can (and must) be customized by a config file.

In general, the downloads are saved in csv files. These are stored in the same directory from where the script has been started. The configuration file needs to be located in this very same directory as well.


Paths
-----
Where should the files be saved to?
Location of config-file: Home?

Accounts
--------
For which accounts should the data be downloaded for?

Modules
-------
Which modules should be executed?

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

For analysis purposesissue analysis. Default: to file in log directory.
