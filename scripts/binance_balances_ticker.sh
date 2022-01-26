source ~/.zshrc
cd $HOME/Repositories/Binance-Reporting
source env/bin/activate
cd binance-reporting
python3 binance_download.py ../config_ticker_only.yaml
exit