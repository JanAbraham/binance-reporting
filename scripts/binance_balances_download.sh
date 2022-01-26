source ~/.zshrc
cd $HOME/Repositories
source env/bin/activate
cd python-binance-reporting/binance-reporting
echo "*** Lets start downloading balances from Binance ***" >> logs/binance_balances_download.log
Date >> logs/binance_balances_download.log
python3 binance_balances_download.py >> logs/binance_balances_download.log
Date >> logs/binance_balances_download.log
echo "*** Finished downloading balances from Binance ***" >> logs/binance_balances_download.log
exit