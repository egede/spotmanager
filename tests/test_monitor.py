import unittest

from unittest import mock
from os.path import join, dirname

from spotmanager.monitor import main


class MonitorTestCase(unittest.TestCase):

    @mock.patch('spotmanager.monitor.argparse')
    @mock.patch('spotmanager.monitor.logging')
    @mock.patch('spotmanager.monitor.RotatingFileHandler')
    @mock.patch('spotmanager.monitor.SlackChannelHandler')
    @mock.patch('spotmanager.monitor.MattermostChannelHandler')
    @mock.patch('spotmanager.monitor.htcondor')
    def test_main(self, mock_condor, mock_MCH, mock_SCH,
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
        m_parse_args.parse_args.return_value.urlfile=''
        
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

        m_schedd = mock.Mock()
        mock_condor.Schedd.return_value = m_schedd
        m_schedd.query.return_value = [ {'JobStatus':1} ]
        m_schedd.history.return_value = [ {'JobStatus': 4,
                                           'JobStartDate' : 123,
                                           'CompletionDate': 999,
                                           'LastRemoteHost': 'host'} ]


        main()
        mock_SCH.assert_called_with('ABC', 'def')
        mock_MCH.assert_called_with('https://test.me')


        m_schedd.query.assert_called()
        m_schedd.history.assert_called()
        
