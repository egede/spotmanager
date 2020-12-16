import unittest

from unittest import mock

from spotmanager.controller import main


class ControllerTestCase(unittest.TestCase):

    @mock.patch('spotmanager.controller.manager')
    def test_main(self, mock_manager):

        main()

        mock_manager.assert_called()
