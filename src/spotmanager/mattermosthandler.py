import os
import logging
import requests

class MattermostChannelHandler(logging.Handler):
    """ Logging handler to send messages to a Mattermost Channel.

        Args:
            url (str)

    """

    def __init__(self, url):
        super(MattermostChannelHandler, self).__init__()

        self.url = url


    def emit(self, record):
        headers = {'Content-Type': 'application/json',}
        values = f'{{ "text": "{self.format(record)}"}}'
        
        try:
            response = requests.post(self.url, headers=headers, data=values) 
        except requests.exceptions.RequestException as e:
            print(f'Mattermost messaging gave error: {e}')

