source ~/.zshrc
cd $HOME/Repositories/Binance-Reporting
source env/bin/activate
cd binance-reporting
echo "*** Lets start downloading data from Binance ***" >> logs/br_download_all.log
Date >> logs/br_download_all.log
python3 binance_download.py >> logs/br_download_all.log
Date >> logs/br_download_all.log
echo "*** Finished downloading data from Binance ***" >> logs/br_download_all.log
exit