source ~/.zshrc
cd $HOME/Repositories/Binance-Reporting
source env/bin/activate
cd binance-reporting
echo "*** Lets start downloading klines from Binance ***" >> logs/binance_klines_download.log
Date >> logs/binance_klines_download.log
python3 binance_klines_download.py >> logs/binance_klines_download.log
Date >> logs/binance_klines_download.log
echo "*** Finished downloading klines from Binance ***" >> logs/binance_klines_download.log
exit