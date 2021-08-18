import os
import time
import json
import socket
import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class SlackChannelHandler(logging.Handler):
    """ Logging handler to send messages to a Slack Channel.

        Args:
            token (str)
            channel (str)

    """

    def __init__(self, token, channel):
        super(SlackChannelHandler, self).__init__()

        self.token = token
        self.channel = channel
        self._slack = WebClient(token=token)


    def emit(self, record):
        try:
            result = self._slack.chat_postMessage(channel=self.channel,
                                                  text=self.format(record))
        except SlackApiError as e:
            print(f'Slack messaging gave error: {e}')

