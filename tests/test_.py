# tests/test_product_categories_processor.py
import unittest
import os
import sys
import asyncio

# Dodanie katalogu głównego projektu do sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import AsyncMock, patch, MagicMock
from src.modules.product_categories_processor import ProductCategoriesProcessingHelper
from src.modules.config_helper import ConfigHelper

class TestProductCategoriesProcessingHelper(unittest.TestCase):
    def setUp(self):
        self.config_file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'config', 'config.json')
        self.config_helper = ConfigHelper(self.config_file_path)
        self.woocommerce_api_domain = "example.com"
        self.woocommerce_alias_product_category = "product-category"
        self.all_categories = [
            {
                "id": 15,
                "name": "Albums",
                "slug": "albums",
                "parent": 11,
                "description": "Test description",
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
        ]
        self.processor = ProductCategoriesProcessingHelper(
            self.all_categories, 
            self.woocommerce_api_domain, 
            self.woocommerce_alias_product_category, 
            self.config_helper
        )

    @patch('src.modules.product_categories_processor.ImageProcessor')
    def test_process_images_in_categories(self, mock_image_processor):
        mock_image_processor_instance = mock_image_processor.return_value
        mock_image_processor_instance.process_images_in_description.return_value = "Processed description with images"

        async def run_test():
            await self.processor.process_images_in_categories()
            self.assertEqual(self.processor.all_categories_process[0]['description_with_img'], "Processed description with images")

        asyncio.run(run_test())

    @patch('src.modules.product_categories_processor.ImageProcessor')
    def test_process_categories(self, mock_image_processor):
        mock_image_processor_instance = mock_image_processor.return_value
        mock_image_processor_instance.process_images_in_description.return_value = "Processed description with images"

        async def run_test():
            processed_categories = await self.processor.process_categories()
            self.assertGreater(len(processed_categories), 0)
            self.assertEqual(processed_categories[0]['description_with_img'], "Processed description with images")
            self.assertIn('category_xpath', processed_categories[0])
            self.assertIn('parent_name', processed_categories[0])
            self.assertIn('parent_slug', processed_categories[0])
            self.assertIn('parent_xpath', processed_categories[0])
            self.assertIn('link', processed_categories[0])
            self.assertIn('display', processed_categories[0])

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
