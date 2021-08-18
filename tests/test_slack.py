import unittest

from unittest import mock

from spotmanager.slackhandler import SlackChannelHandler
from slack_sdk.errors import SlackApiError

class SlackTestCase(unittest.TestCase):

    @mock.patch('spotmanager.slackhandler.WebClient')
    def test_main(self, mock_webclient):

        token = 'testtoken'
        m = mock.Mock()
        mock_webclient.return_value=m

        s = SlackChannelHandler(token,'testchannel')
        s.format = mock.Mock()
        s.format.return_value='formatted text'
        
        assert(s.token == token)
        assert(s.channel == 'testchannel')
        mock_webclient.assert_called_with(token=token)

        s.emit('abc')
        s.format.assert_called()
        m.chat_postMessage.assert_called_with(channel='testchannel',
                                              text='formatted text')
        
        m2 = mock.Mock()
        m.chat_postMessage = m2
        m2.side_effect = SlackApiError('a', 'b')
        s.emit('abc')


