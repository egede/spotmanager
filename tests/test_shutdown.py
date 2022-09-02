import unittest

from unittest import mock
from os.path import join, dirname

from spotmanager.shutdown import main


class ShutdownTestCase(unittest.TestCase):

    @mock.patch('spotmanager.shutdown.argparse')
    @mock.patch('spotmanager.shutdown.logging')
    @mock.patch('spotmanager.shutdown.RotatingFileHandler')
    @mock.patch('spotmanager.shutdown.SlackChannelHandler')
    @mock.patch('spotmanager.monitor.MattermostChannelHandler')

    def test_main(self, mock_MCH, mock_SCH,
                  mock_RFH, mock_logging, mock_argparse):

        m_DEBUG = mock.Mock()
        m_INFO = mock.Mock()
        mock_logging.DEBUG = m_DEBUG
        mock_logging.INFO = m_INFO
        m_getLogger = mock.Mock()
        mock_logging.getLogger.return_value = m_getLogger
        
        m_args = mock.Mock()
        
        m_parse_args = mock.Mock()
        m_parse_args.parse_args.return_value.verbose=1

        mock_argparse.ArgumentParser.return_value = m_parse_args
        m_parse_args.parse_args.return_value.stdout= None
        m_parse_args.parse_args.return_value.tokenfile=''
        
        main()

        mock_RFH.assert_called()
        m_getLogger.setLevel.assert_called_with(m_DEBUG)

        m_parse_args.parse_args.return_value.verbose=None
        main()
        m_getLogger.setLevel.assert_called_with(m_INFO)

        m_parse_args.parse_args.return_value.stdout=1
        main()
        mock_logging.StreamHandler.assert_called()

        fname = join(dirname(__file__), 'test_monitor_token')
        m_parse_args.parse_args.return_value.tokenfile=fname
        m_parse_args.parse_args.return_value.channel='def'

        fname = join(dirname(__file__), 'test_mattermost_url')
        m_parse_args.parse_args.return_value.urlfile=fname

        main()
        mock_SCH.assert_called_with('ABC', 'def')
        mock_MCH.assert_called_with('https://test.me')
