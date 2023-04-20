import requests
BOT_TOKEN = '5930782774:AAHxSbja0OQRCyo8ZP5vEXWKSG-RYEpQS-Y'
# Telegram chat ID
CHAT_ID = '5249309539'
def send_alert(message):
    '''
    Function to send alert messages to Telegram chat using Telegram bot
    Parameters:
    message (str): message to be sent to Telegram chat
    '''
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, json=data)
