import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import requests

# Add the parent directory to the sys.path to allow for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.pihole.pihole import PiHoleOverlord

class TestPiHoleOverlord(unittest.TestCase):
    def setUp(self):
        self.mock_app_config = {
            "remote_pi_list": ["pi.hole"],
            "domains": {
                "test_block": ["example.com", "test.com"]
            },
            "remote_pi_password": "password",
            "remote_pi_token": "token",
        }
        # We patch first_connect to avoid network calls during initialization of most tests
        with patch.object(PiHoleOverlord, 'first_connect', return_value=None):
            self.pihole_overlord = PiHoleOverlord(app_config=self.mock_app_config)
            self.pihole_overlord.sessions = {'pi.hole': MagicMock()}
            self.pihole_overlord.logged_in = True # Assume logged in for most tests

    # Test first_connect separately
    @patch('lib.pihole.base.requests.Session')
    def test_first_connect_success(self, mock_session):
        mock_response = MagicMock()
        # No need to set status_code, as raise_for_status won't raise by default on a mock
        mock_session.return_value.post.return_value = mock_response

        # Need a fresh instance for this test
        pihole_overlord = PiHoleOverlord(app_config=self.mock_app_config)
        pihole_overlord.first_connect()
        self.assertTrue(pihole_overlord.logged_in)

    @patch('lib.pihole.base.requests.Session')
    def test_first_connect_failure(self, mock_session):
        mock_post = mock_session.return_value.post
        mock_post.side_effect = requests.exceptions.RequestException("Test Failure")

        # Need a fresh instance for this test
        pihole_overlord = PiHoleOverlord(app_config=self.mock_app_config)
        pihole_overlord.first_connect()
        self.assertFalse(pihole_overlord.logged_in)

    @patch.object(PiHoleOverlord, 'sGet')
    def test_get_status_on(self, mock_sGet):
        mock_response = {
            "data": [
                {"domain": r"(\.|^)example\.com$", "enabled": 1},
                {"domain": r"(\.|^)test\.com$", "enabled": 0}
            ]
        }
        mock_sGet.return_value = mock_response

        status = self.pihole_overlord.get("test_block")
        self.assertEqual(status, {"status": "on"})

    @patch.object(PiHoleOverlord, 'sGet')
    def test_get_status_off(self, mock_sGet):
        mock_response = {
            "data": [
                {"domain": r"(\.|^)example\.com$", "enabled": 0},
                {"domain": r"(\.|^)test\.com$", "enabled": 0}
            ]
        }
        mock_sGet.return_value = mock_response

        status = self.pihole_overlord.get("test_block")
        self.assertEqual(status, {"status": "off"})

    @patch.object(PiHoleOverlord, 'get', return_value={"status": "off"})
    @patch.object(PiHoleOverlord, 'cmd')
    def test_post_disable(self, mock_cmd, mock_get):
        self.pihole_overlord.post("disable", "test_block")

        mock_cmd.assert_any_call("add", "regex_black", pi="pi.hole", domain=r"(\.|^)example\.com$")
        mock_cmd.assert_any_call("add", "regex_black", pi="pi.hole", domain=r"(\.|^)test\.com$")

    @patch.object(PiHoleOverlord, 'get', return_value={"status": "on"})
    @patch.object(PiHoleOverlord, 'cmd')
    def test_post_enable(self, mock_cmd, mock_get):
        self.pihole_overlord.post("enable", "test_block")

        mock_cmd.assert_any_call("sub", "regex_black", pi="pi.hole", domain=r"(\.|^)example\.com$")
        mock_cmd.assert_any_call("sub", "regex_black", pi="pi.hole", domain=r"(\.|^)test\.com$")

if __name__ == '__main__':
    unittest.main()