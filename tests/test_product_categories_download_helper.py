# tests/test_product_categories_download_helper.py
import unittest
import os
import sys
import asyncio

# Dodanie katalogu głównego projektu do sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import AsyncMock, patch, MagicMock
from src.modules.product_categories_download_helper import CategoriesDownloadHelper
from src.modules.config_helper import ConfigHelper

class TestCategoriesDownloadHelper(unittest.TestCase):
    def setUp(self):
        self.config_file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'config', 'config.json')
        self.config_helper = ConfigHelper(self.config_file_path)
        self.session = AsyncMock()
        self.helper = CategoriesDownloadHelper(self.session, self.config_helper)

    @patch('httpx.AsyncClient.get')
    @patch('httpx.AsyncClient.head')
    def test_pobieranie_wszystkich_kategorii(self, mock_head, mock_get):
        async def run_test():
            # Mockowanie odpowiedzi HTTP HEAD
            mock_head_response = MagicMock()
            mock_head_response.status_code = 200
            mock_head_response.headers = {
                'X-WP-Total': '4',  # Zmieniono na 4, aby pasowało do liczby kategorii
                'X-WP-TotalPages': '2'  # 2 strony po 2 kategorie
            }
            mock_head.return_value = mock_head_response

            # Mockowanie odpowiedzi HTTP GET dla różnych stron
            mock_get.side_effect = [
                MagicMock(status_code=200, json=MagicMock(return_value=[
                    {
                        "id": 15,
                        "name": "Albums",
                        "slug": "albums",
                        "parent": 11,
                        "description": "",
                        "display": "default",
                        "image": [],
                        "menu_order": 0,
                        "count": 4,
                        "_links": {
                            "self": [
                                {
                                    "href": "https://example.com/wp-json/wc/v3/products/categories/15"
                                }
                            ],
                            "collection": [
                                {
                                    "href": "https://example.com/wp-json/wc/v3/products/categories"
                                }
                            ],
                            "up": [
                                {
                                    "href": "https://example.com/wp-json/wc/v3/products/categories/11"
                                }
                            ]
                        }
                    },
                    {
                        "id": 9,
                        "name": "Clothing",
                        "slug": "clothing",
                        "parent": 0,
                        "description": "",
                        "display": "default",
                        "image": {
                            "id": 730,
                            "date_created": "2017-03-23T00:01:07",
                            "date_created_gmt": "2017-03-23T03:01:07",
                            "date_modified": "2017-03-23T00:01:07",
                            "date_modified_gmt": "2017-03-23T03:01:07",
                            "src": "https://example.com/wp-content/uploads/2017/03/T_2_front.jpg",
                            "name": "",
                            "alt": ""
                        },
                        "menu_order": 0,
                        "count": 36,
                        "_links": {
                            "self": [
                                {
                                    "href": "https://example/wp-json/wc/v3/products/categories/9"
                                }
                            ],
                            "collection": [
                                {
                                    "href": "https://example/wp-json/wc/v3/products/categories"
                                }
                            ]
                        }
                    }
                ])),
                MagicMock(status_code=200, json=MagicMock(return_value=[
                    {
                        "id": 10,
                        "name": "Hoodies",
                        "slug": "hoodies",
                        "parent": 9,
                        "description": "",
                        "display": "default",
                        "image": [],
                        "menu_order": 0,
                        "count": 6,
                        "_links": {
                            "self": [
                                {
                                    "href": "https://example.com/wp-json/wc/v3/products/categories/10"
                                }
                            ],
                            "collection": [
                                {
                                    "href": "https://example.com/wp-json/wc/v3/products/categories"
                                }
                            ],
                            "up": [
                                {
                                    "href": "https://example.com/wp-json/wc/v3/products/categories/9"
                                }
                            ]
                        }
                    },
                    {
                        "id": 11,
                        "name": "Music",
                        "slug": "music",
                        "parent": 0,
                        "description": "",
                        "display": "default",
                        "image": [],
                        "menu_order": 0,
                        "count": 7,
                        "_links": {
                            "self": [
                                {
                                    "href": "https://example.com/wp-json/wc/v3/products/categories/11"
                                }
                            ],
                            "collection": [
                                {
                                    "href": "https://example.com/wp-json/wc/v3/products/categories"
                                }
                            ]
                        }
                    }
                ]))
            ]
            
            endpoint = f"https://{self.config_helper.WOOCOMMERCE_API_DOMAIN}/wp-json/wc/v3/products/categories"
            categories = await self.helper.pobieranie_wszystkich_kategorii(endpoint)
            
            # Debugowanie
            print("Categories:", categories)
            
            self.assertEqual(len(categories), 4)
        
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
