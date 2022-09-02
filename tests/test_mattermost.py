import unittest
import requests
import logging

from unittest import mock
from requests.exceptions import RequestException

from spotmanager.mattermosthandler import MattermostChannelHandler


class mattermostTestCase(unittest.TestCase):

    @mock.patch('requests.post')
    def test_main(self, mock_post):

        url = 'testurl'

        mm = MattermostChannelHandler(url)
        
        assert(mm.url == url)

        record = logging.makeLogRecord(dict(msg='abc'))

        mm.emit(record)
        mock_post.assert_called_with('testurl', 
                                  headers={'Content-Type': 'application/json',},
                                  data='{ "text": "abc"}')
        
        mock_post.side_effect = RequestException()
        mm.emit(record)
