import os
import logging
import telegram.ext     # sending balance information to telegram
try:
    from binance_reporting.downloader import balances
except:
    from downloader import balances

def send_bal(accounts, account_groups, telegram_token):
    """ sending short balance status msg to telegram channels
    """

    logging.info(' - Sending balance tickers to telegram channels. -')
    for account in accounts:

        account_details = accounts[account]
        PUBLIC = os.environ.get(account_details['osvar_api_public'])
        SECRET = os.environ.get(account_details['osvar_api_secret'])

        balance = balances(account, account_details['type'], PUBLIC, SECRET)

        account_details['cash'] = round(balance['cash'], 1)
        account_details['portval'] = round(balance['portval'], 1)
        account_details['profit'] = round((balance['portval'] - account_details['investment']) / account_details['investment']*100, 2) if account_details['investment'] != 0 else 0

        strCash = 'C=' + str(account_details['cash'])
        strPortVal = 'B=' + str(account_details['portval'])
        strProfit = 'P=' + str(account_details['profit']) + '%'

        bot = telegram.Bot(token = telegram_token)
        bot_text = (strCash + ' ' + strPortVal + ' ' + strProfit + ' ' + account_details['chat_pseudo']).lower()
        bot.send_message(chat_id = account_details['chat_id'], text = bot_text)

    logging.info(' - Finished sending tickers for all listed accounts! -')

    logging.info(' - Looping through different account groups and sending ticker messages to telegram for every group -')

    for account_group in account_groups:
        account_group = account_groups[account_group]
        chat_id = account_group['chat_id']
        chat_pseudo = account_group['chat_pseudo']
        investment = 0
        cash = 0
        portval = 0

        # get details for every account and sum them up
        for account in account_group['accounts']:
            account_details = accounts[account]
            investment = investment + account_details['investment']
            cash = cash + account_details['cash']
            portval = portval + account_details['portval']

        strCash = 'C=' + str(round(cash, 0))
        strPortVal = 'B=' + str(round(portval, 0))
        strProfit = 'P=' + str(round((portval - investment) / investment * 100, 1)) + '%'

        bot_text = (strCash + ' ' + strPortVal + ' ' + strProfit + ' ' + chat_pseudo).lower()
        bot.send_message(chat_id = chat_id, text = bot_text)

    logging.info(' - Finished sending Tickers to groups -')