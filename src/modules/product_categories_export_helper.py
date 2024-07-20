import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any

class ProductCategoriesExportHelper:
    def __init__(self, config):
        self.config = config
        self.current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def export_categories(self, all_categories: List[Dict[str, Any]], all_categories_process: List[Dict[str, Any]], all_categories_transformed: List[Dict[str, Any]]):
        self._export_to_json_and_csv(all_categories, "woocommerce_all_categories")
        self._export_to_json_and_csv(all_categories_process, "woocommerce_all_categories_processed")
        self._export_to_json_and_csv(all_categories_transformed, "woocommerce_all_categories_transformed")

    def _export_to_json_and_csv(self, data: List[Dict[str, Any]], base_filename: str):
        json_filename = f"{base_filename}_{self.current_date}.json"
        csv_filename = f"{base_filename}_{self.current_date}.csv"

        # Export to JSON
        json_path = os.path.join(self.config.OUTPUT_DATA_FOLDER_FOR_CATEGORIES, json_filename)
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

        # Export to CSV
        csv_path = os.path.join(self.config.OUTPUT_CSV_FOLDER_FOR_CATEGORIES, csv_filename)
        if data:
            keys = data[0].keys()
            with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=keys)
                writer.writeheader()
                for row in data:
                    writer.writerow(row)

    def _ensure_directory_exists(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)