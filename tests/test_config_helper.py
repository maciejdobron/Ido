# tests/test_config_helper.py
import unittest
import os
import sys

# Dodanie katalogu głównego projektu do sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.modules.config_helper import ConfigHelper

class TestConfigHelper(unittest.TestCase):
    def setUp(self):
        self.config_file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'config', 'config.json')
        self.config_helper = ConfigHelper(self.config_file_path)

    def test_initialization(self):
        self.assertEqual(self.config_helper.WOOCOMMERCE_API_DOMAIN, 'woocommerce.design4art.pl')
        self.assertEqual(self.config_helper.WOOCOMMERCE_API_CONSUMER_KEY, 'ck_c972fc2a2610bbcce0daddba5f27e967ad27dafc')

    def test_create_directories(self):
        self.config_helper.create_directories()
        self.assertTrue(os.path.exists(self.config_helper.OUTPUT_DATA_FOLDER))
        self.assertTrue(os.path.exists(self.config_helper.OUTPUT_CSV_FOLDER))

if __name__ == '__main__':
    unittest.main()