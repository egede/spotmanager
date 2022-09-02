import unittest

from unittest import mock
from requests.exceptions import RequestException

from spotmanager.mattermosthandler import MattermostChannelHandler


class mattermostTestCase(unittest.TestCase):

    @mock.patch('spotmanager.mattermosthandler.requests')
    def test_main(self, mock_requests):

        url = 'testurl'
        m = mock.Mock()
        mock_requests.return_value=m

        mm = MattermostChannelHandler(url)
        mm.format = mock.Mock()
        mm.format.return_value='formatted text'
        
        assert(mm.url == url)

        mm.emit('abc')
        m.post.assert_called_with(url='testurl', 
                                  headers={'Content-Type': 'application/json',},
                                  data='{ "text": "abc"}')
        
        m2 = mock.Mock()
        m.post = m2
        m2.side_effect = RequestException()
        m.emit('abc')
