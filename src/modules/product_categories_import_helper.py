import os
import re
import json
import time
import asyncio
import httpx
import glob
from datetime import datetime
from rich.console import Console
from rich.progress import Progress

from .config_helper import ConfigHelper
from .language_conversion import convert_lang_codes

class ProductCategoriesImportHelper:
    def __init__(self, config, idosell_api_key):
        self.config = config
        self.idosell_api_key = idosell_api_key
        self.idosell_api_category_url = f"https://{config.IDOSELL_API_DOMAIN}/api/admin/v3/products/categories"
        self.json_output_folder_for_categories = config.OUTPUT_DATA_FOLDER_FOR_CATEGORIES
        self.logs_output_folder_for_categories = config.OUTPUT_LOGS_FOLDER_FOR_CATEGORIES
        self.supported_languages = getattr(config, 'SUPPORTED_LANGUAGES', ['pl', 'en'])  # domyślnie polski i angielski
        self.console = Console()

    async def import_categories_into_idosell_as_product_categories_in_the_panel(self, all_categories_transformed):
        if not all_categories_transformed:
            # Szukamy najnowszego pliku z transformowanymi kategoriami
            pattern = os.path.join(self.output_data_folder_for_categories, 'woocommerce_all_categories_transformed_*.json')
            files = glob.glob(pattern)
            if not files:
                self.console.print("[bold red]Nie znaleziono pliku z transformowanymi kategoriami.[/bold red]")
                return
            
        sorted_categories = self.sort_categories_by_hierarchy(all_categories_transformed)
        
        category_mapping = {"0": 0}
        added_count = existed_count = failed_count = error_count = processed_count = 0
        total_elapsed_time = 0

        for category in sorted_categories:
            category_xpath = category.get('category_xpath', 'Unknown')
            
            start_time = time.time()

            status_message = f"[bold cyan]Importowanie kategorii [bold blue]\"{category_xpath}\"[/bold blue][/bold cyan]"
            with self.console.status(status_message, spinner="dots6", spinner_style="bold cyan", speed=1.0):
                response_text, added, existed, failed, processed = await self.add_batch_of_categories([category], category_mapping, 'hierarchy')

                end_time = time.time()
                elapsed_time = end_time - start_time
                total_elapsed_time += elapsed_time

                added_count += added
                existed_count += existed
                failed_count += failed
                processed_count += processed
                                   
                if response_text:
                    error_count += 1
                    self.console.print(f"[bold red]▣[/bold red] Status [bold red]niepowodzenie[/bold red] : Import kategorii o ścieżce [bold red]{category_xpath}[/bold red] nie powiódł się (czas próby: [bold yellow]{elapsed_time:.2f}[/bold yellow] sekund).", style="white")
                else:
                    self.console.print(f"▣ Zaimportowano kategorię o ścieżce [bold blue]\"{category_xpath}\"[/bold blue] (czas: [bold green]{elapsed_time:.2f}[/bold green] sekund).", style="bold cyan")
                    
        self.print_import_summary(processed_count, added_count, existed_count, failed_count, total_elapsed_time)
    
    async def add_batch_of_categories(self, categories, category_mapping, batch_type):
        added_count = existed_count = failed_count = processed_count = 0
        error_text = None
        cache_file = os.path.join(self.json_output_folder_for_categories, 'category_cache.json')
        category_cache = self.load_category_cache(cache_file)

        async with httpx.AsyncClient() as client:
            for category in categories:
                payload = self.prepare_category_payload(category, category_mapping)
                headers = {
                    "accept": "application/json",
                    "content-type": "application/json",
                    "X-API-KEY": self.idosell_api_key
                }

                response = await client.put(self.idosell_api_category_url, json=payload, headers=headers)

                if response.status_code == 200:
                    response_data = response.json()
                    added, existed, failed = await self.process_api_response(response_data, category, category_mapping, category_cache, client)
                    added_count += added
                    existed_count += existed
                    failed_count += failed
                    processed_count += 1
                else:
                    error_text = response.text
                    self.console.print(f"Błąd przy dodawaniu kategorii: {error_text}", style="bold red")

                self.log_api_interaction(category, payload, headers, response)

        self.save_category_cache(cache_file, category_cache)
        return error_text, added_count, existed_count, failed_count, processed_count

    def prepare_category_payload(self, category, category_mapping):
        return {
            "params": {
                "categories": [
                    {
                        "lang_data": [
                            {
                                "lang_id": convert_lang_codes(lang_code),
                                "singular_name": category.get('translations', {}).get(lang_code, {}).get('category_name', category['category_name']),
                                "plural_name": category.get('translations', {}).get(lang_code, {}).get('category_name', category['category_name'])
                            } for lang_code in self.supported_languages if 'translations' in category and lang_code in category.get('translations', {}) or lang_code == category.get('lang', 'pl')
                        ],
                        "operation": "add",
                        "parent_id": category_mapping.get(str(category['parent_id']), 0),
                    }
                ]
            }
        }

    async def process_api_response(self, response_data, category, category_mapping, category_cache, client):
        added = existed = failed = 0
        for api_category in response_data['result']['categories']:
            category_id = str(category['category_id'])
            if 'faultCode' in api_category and api_category['faultCode'] == 20:
                existing_category_id = api_category['id']
                updated = await self.update_existing_category(category, existing_category_id, category_cache, client, category_mapping)
                if updated:
                    existed += 1
                else:
                    failed += 1
            else:
                category_mapping[category_id] = api_category['id']
                added += 1

            category_xpath = category.get('category_xpath', '')
            self.console.print(
                f"[yellow]★[/yellow] "
                f"Przetwarzanie category_id: {category_id}, category_xpath: {category_xpath}", 
                style="yellow"
            )

            category_cache[category_id] = {
                "category_name": category['category_name'],
                "category_xpath": category_xpath,
                "id": api_category['id'],
                "parent_id": api_category['parent_id']
            }
        return added, existed, failed

    async def update_existing_category(self, category, existing_category_id, category_cache, client, category_mapping):
        cache_entry = category_cache.get(str(category['category_id']))
        if cache_entry:
            payload = {
                "params": {
                    "categories": [
                        {
                            "operation": "edit",
                            "priority": "priority",
                            "id": cache_entry['id'],
                            "parent_id": cache_entry['parent_id'],
                            "lang_data": [
                                {
                                    "lang_id": convert_lang_codes(lang_code),
                                    "singular_name": category.get('translations', {}).get(lang_code, {}).get('category_name', category['category_name']),
                                    "plural_name": category.get('translations', {}).get(lang_code, {}).get('category_name', category['category_name'])
                                } for lang_code in self.supported_languages if 'translations' in category and lang_code in category.get('translations', {}) or lang_code == category.get('lang', 'pl')
                            ]
                        }
                    ]
                }
            }
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "X-API-KEY": self.idosell_api_key
            }
            response = await client.put(self.idosell_api_category_url, json=payload, headers=headers)
            if response.status_code == 200:
                category_mapping[str(category['category_id'])] = existing_category_id
                return True
            else:
                self.console.print(f"Błąd przy aktualizacji kategorii: {response.text}", style="bold red")
                return False

    def log_api_interaction(self, category, payload, headers, response):
        api_log = {
            "request": {
                "url": self.idosell_api_category_url,
                "payload": payload,
                "headers": headers
            },
            "response": {
                "status": response.status_code,
                "data": response.json() if response.status_code == 200 else response.text
            }
        }

        os.makedirs(self.logs_output_folder_for_categories, exist_ok=True)
        log_filename = f'api_category_{self.normalize_filename(category["category_name"])}_{category["category_id"]}.json'
        log_filepath = os.path.join(self.logs_output_folder_for_categories, log_filename)
        with open(log_filepath, 'w', encoding='utf-8') as file:
            json.dump(api_log, file, indent=4, ensure_ascii=False)

    def print_import_summary(self, processed_count, added_count, existed_count, failed_count, total_elapsed_time):
        self.console.print("\nPodsumowanie importu:", style="cyan")
        self.console.print(f"▪️ Liczba węzłów przetworzonych jako [cyan]\"Kategorii towarów w panelu IdoSell\"[/cyan]: [bold cyan]{processed_count}[/bold cyan]")
        self.console.print(f"▪️ Dodano [bold green]{added_count}[/bold green] nowych węzłów menu")
        self.console.print(f"▪️ Zaktualizowano [bold cyan]{existed_count}[/bold cyan] istniejących węzłów")
        self.console.print(f"▪️ Import nie powiódł się dla [bold red]{failed_count}[/bold red] węzłów")
        self.console.print(f"Całkowity czas wykonania operacji wyniósł [bold green]{total_elapsed_time:.2f}[/bold green] sekundy", style="cyan")
        self.console.print()

    def sort_categories_by_hierarchy(self, categories):
        return sorted(categories, key=lambda x: x['category_xpath'])

    def load_category_cache(self, cache_file):
        if (os.path.exists(cache_file)):
            with open(cache_file, 'r') as file:
                return json.load(file)
        return {}

    def save_category_cache(self, cache_file, category_cache):
        #self.console.print(f"Zapisuję cache do: {cache_file}", style="green")
        with open(cache_file, 'w') as file:
            json.dump(category_cache, file, indent=4)  # Dodano indent=4 dla lepszej czytelności

    def normalize_filename(self, filename):
        return re.sub(r'[^\w\-_.]', '_', filename)
