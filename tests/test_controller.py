import unittest

from unittest import mock

from spotmanager.controller import main


class ControllerTestCase(unittest.TestCase):

    @mock.patch('spotmanager.controller.argparse')
    @mock.patch('spotmanager.controller.logging')
    @mock.patch('spotmanager.controller.RotatingFileHandler')
    @mock.patch('spotmanager.controller.manager')
    def test_main(self, mock_manager, mock_RFH, mock_logging, mock_argparse):

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
        
        main()

        mock_manager.assert_called()
        mock_RFH.assert_called()
        m_getLogger.setLevel.assert_called_with(m_DEBUG)

        m_parse_args.parse_args.return_value.verbose=None
        main()
        m_getLogger.setLevel.assert_called_with(m_INFO)

        m_parse_args.parse_args.return_value.stdout=1
        main()
        mock_logging.StreamHandler.assert_called()

        
