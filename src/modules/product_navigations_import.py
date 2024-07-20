# product_navigations_import.py

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

class ProductNavigationsImport:
    def __init__(self, config: ConfigHelper):
        self.config = config
        self.idosell_api_key = config.IDOSELL_API_KEY
        self.idosell_api_menu_gate_url = config.IDOSELL_API_MENU_GATE_URL
        self.output_data_folder_for_categories = config.OUTPUT_DATA_FOLDER_FOR_CATEGORIES
        self.output_data_folder_for_menu = config.OUTPUT_DATA_FOLDER_FOR_MENU
        self.output_logs_folder_for_menu = config.OUTPUT_LOGS_FOLDER_FOR_MENU
        self.supported_languages = config.SUPPORTED_LANGUAGES
        self.console = Console()

    async def import_categories_into_idosell_as_navigation_menu_in_shop(self, all_categories_transformed):
        if not all_categories_transformed:
            # Szukamy najnowszego pliku z transformowanymi kategoriami
            pattern = os.path.join(self.output_data_folder_for_categories, 'woocommerce_all_categories_transformed_*.json')
            files = glob.glob(pattern)
            if not files:
                self.console.print("[bold red]Nie znaleziono pliku z transformowanymi kategoriami.[/bold red]")
                return

        sorted_categories = self.sort_categories_by_hierarchy(all_categories_transformed)

        shop_id = self.console.input("[bold cyan]▣ Podaj identyfikator sklepu ([bold bright_white]domyślnie:[/bold bright_white] [bold bright_blue]1[/bold bright_blue]):[/bold cyan] ") or "1"
        menu_id = self.console.input("[bold cyan]▣ Podaj identyfikator menu ([bold bright_white]domyślnie:[/bold bright_white] [bold bright_blue]1[/bold bright_blue]):[/bold cyan] ") or "1"
        lang_id = self.console.input("[bold cyan]▣ Podaj identyfikator języka ([bold bright_white]domyślnie:[/bold bright_white] [bold bright_blue]pol[/bold bright_blue]): ") or "pol"
        desc_mode = self.console.input("[bold cyan]▣ Wskaż położenie opisu menu ([bold bright_white]domyślnie:[/bold bright_white] [bold bright_blue]up[/bold bright_blue]): ") or "up"
        self.description_position = "description" if desc_mode.lower() == "up" else "description_bottom"

        self.console.print()

        category_mapping = {"0": 0}
        added_count = existed_count = failed_count = error_count = processed_count = 0
        total_elapsed_time = 0

        for category in sorted_categories:
            category_xpath = category.get('category_xpath', 'Unknown')
            path_levels = category_xpath.split('\\')

            if len(path_levels) > 8:
                self.console.print(f"[bold red]▣[/bold red] Kategoria o ścieżce [cyan]\"{category_xpath}\"[/cyan] przekracza dozwoloną liczbę 8 poziomów. Kategoria nie zostanie zaimportowana.", style="bold red")
                failed_count += 1
                continue

            start_time = time.time()
            
            status_message = f"[bold cyan]Importowanie menu [bold blue]\"{category_xpath}\"[/bold blue][/bold cyan]"
            with self.console.status(status_message, spinner="dots6", spinner_style="bold cyan", speed=1.0):
                response_text, added, existed, failed, processed = await self.add_batch_of_menu([category], category_mapping, shop_id, menu_id, lang_id, 'hierarchy')
                
                end_time = time.time()
                elapsed_time = end_time - start_time
                total_elapsed_time += elapsed_time

                added_count += added
                existed_count += existed
                failed_count += failed
                processed_count += processed

                if response_text:
                    error_count += 1
                    self.console.print(
                        f"[bold red]✦[/bold red]",
                        f"Import menu o ścieżce: [bold red]\"{category_xpath}\"[/bold red] nie powiódł się (czas próby: [bold blue]{elapsed_time:.2f}[/bold blue] sekund).",
                        style="white"
                    )
                else:
                    self.console.print(
                        f"[bold green]✦[/bold green] "
                        f"Zaimportowano menu o ścieżce: [bold blue]\"{category_xpath}\"[/bold blue] (czas: [bold blue]{elapsed_time:.2f}[/bold blue] sekund).",
                        style="green"
                    )

        self.print_import_summary(processed_count, added_count, existed_count, failed_count, total_elapsed_time)
    
    async def add_batch_of_menu(self, categories, category_mapping, shop_id, menu_id, custom_lang_id, batch_type):
        added_count = existed_count = failed_count = processed_count = 0
        error_text = None
        cache_file = os.path.join(self.output_data_folder_for_menu, 'menu_cache.json')
        menu_cache = self.load_menu_cache(cache_file)

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            for category in categories:
                path_levels = category['category_xpath'].split('\\')
                if len(path_levels) > 8:
                    self.console.print(
                        f"[bold red]▣[/bold red] Kategoria o ścieżce [cyan]{category['category_xpath']}[/cyan] przekracza dozwoloną liczbę 8 poziomów. Kategoria nie zostanie zaimportowana.",
                        style="bold red"
                    )
                    failed_count += 1
                    continue

                parent_xpath = '\\'.join(category['category_xpath'].split('\\')[:-1])
                if category_mapping.get(parent_xpath, "0") == "0" and parent_xpath:
                    success, new_parent_id = await self.add_single_category({"category_xpath": parent_xpath}, shop_id, menu_id, custom_lang_id, category_mapping)
                    if success:
                        category_mapping[parent_xpath] = new_parent_id
                    else:
                        failed_count += 1
                        continue

                payload = self.prepare_menu_payload(category, category_mapping, shop_id, menu_id, custom_lang_id)
                headers = {
                    "accept": "application/json",
                    "content-type": "application/json",
                    "X-API-KEY": self.idosell_api_key
                }

                response = await client.post(self.idosell_api_menu_gate_url, json=payload, headers=headers)
                if response.status_code == 200:
                    response_data = response.json()
                    added, existed, failed = await self.process_api_response(response_data, category, category_mapping, menu_cache, client, shop_id, menu_id, custom_lang_id, headers)
                    added_count += added
                    existed_count += existed
                    failed_count += failed
                    processed_count += 1
                else:
                    error_text = response.text
                    # self.console.print(
                    #     f"✦ "
                    #     #f"Błąd przy dodawaniu kategorii menu: {error_text}",
                    #     f"Import menu o ścieżce [bold red]{category['category_xpath']}[/bold red] nie powiódł się.",
                    #     style="bold red"
                    # )
                    failed_count += 1

                self.log_api_interaction(category, payload, headers, response)

        self.save_menu_cache(cache_file, menu_cache)
        return error_text, added_count, existed_count, failed_count, processed_count

    def prepare_menu_payload(self, category, category_mapping, shop_id, menu_id, custom_lang_id):
        category_xpath = category['category_xpath']
        parent_xpath = '\\'.join(category_xpath.split('\\')[:-1])
        parent_id = category_mapping.get(parent_xpath, "0")

        lang_data = []
        for lang_code in self.supported_languages:
            lang_specific_data = category.get('translations', {}).get(lang_code, category)
            lang_data.append({
                "lang_id": convert_lang_codes(lang_code),
                "name": lang_specific_data.get('category_name', ''),
                "priority": lang_specific_data.get('priority', 1),
                self.description_position: lang_specific_data.get('description', ''),
                "item_type": lang_specific_data.get('item_type', ''),
                "meta_title": lang_specific_data.get('category_seo_title', ''),
                "meta_description": lang_specific_data.get('category_seo_description', ''),
                "meta_keywords": lang_specific_data.get('category_seo_keywords', ''),
                "href_target": "_self",
                "hidden": "n",
                "url": lang_specific_data.get('category_url', '')
            })

        return {
            "settings": {"textid_separator": "\\"},
            "menu_list": [{
                "shop_id": shop_id,
                "menu_id": menu_id,
                "item_textid": category_xpath,
                "parent_id": parent_id,
                "parent_textid": parent_xpath,
                "lang_data": lang_data
            }]
        }

    async def process_api_response(self, response_data, category, category_mapping, menu_cache, client, shop_id, menu_id, custom_lang_id, headers):
        added = existed = failed = 0
        for api_category in response_data.get('result', []):
            item_textid = api_category.get('item_textid')
            fault_code = api_category.get('faultCode')
            category_id = str(category['category_id'])
            if fault_code == 0:
                added += 1
                category_mapping[item_textid] = api_category.get('item_id')
                menu_cache[item_textid] = {
                    "category_name": category['category_name'],
                    "category_xpath": category['category_xpath'],
                    "id": api_category.get('item_id'),
                    "parent_id": api_category.get('parent_id')
                }
                
                category_xpath = category.get('category_xpath', '')
                self.console.print(
                    f"⭐ "
                    f"Przetwarzanie category_id: {category_id}, category_xpath: {category_xpath}", 
                    style="yellow"
                )                
            elif fault_code == 2:
                self.console.print(f"Błąd przy dodawaniu menu {item_textid}: Błędny identyfikator języka", style="bold red")
                failed += 1
            elif fault_code == 4:
                self.console.print(f"Błąd przy dodawaniu menu {item_textid}: Wskazanie nieistniejącego rodzica", style="bold red")
                failed += 1
            elif fault_code == 6:
                existed += 1
                existing_menu_id = await self.extract_menu_id_from_error(item_textid, shop_id, menu_id, custom_lang_id)
                if existing_menu_id is not None:
                    category_mapping[item_textid] = existing_menu_id
                    await self.update_existing_menu(category, shop_id, menu_id, custom_lang_id, existing_menu_id, client, headers)
            else:
                self.console.print(f"Błąd przy dodawaniu menu {item_textid}: Nieznany kod błędu {fault_code}", style="bold red")
                failed += 1
        return added, existed, failed

    async def update_existing_menu(self, category, shop_id, menu_id, custom_lang_id, existing_menu_id, client, headers):
        update_payload = self.prepare_menu_payload(category, {category['category_xpath']: existing_menu_id}, shop_id, menu_id, custom_lang_id)
        update_response = await client.put(self.idosell_api_menu_gate_url, json=update_payload, headers=headers)
        
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.log_api_interaction(category, update_payload, headers, update_response, timestamp, is_update=True)

        if update_response.status_code != 200:
            self.console.print(f"Błąd przy aktualizacji kategorii: {update_response.text}", style="bold red")

    def log_api_interaction(self, category, payload, headers, response):
        log_data = {
            "request": {
                "url": self.idosell_api_menu_gate_url,
                "payload": payload,
                "headers": headers
            },
            "response": {
                "status": response.status_code,
                "data": response.json() if response.status_code == 200 else response.text
            }
        }
        
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        log_filename = f'menu_api_log_{self.normalize_filename(category["category_name"])}_{category["category_id"]}.json'
        log_filepath = os.path.join(self.output_logs_folder_for_menu, log_filename)
        os.makedirs(os.path.dirname(log_filepath), exist_ok=True)
        
        with open(log_filepath, 'w', encoding='utf-8') as file:
            json.dump(log_data, file, indent=4, ensure_ascii=False)
        
    def print_import_summary(self, processed_count, total_added, total_existed, failure_count, total_elapsed_time):
        self.console.print("\nPodsumowanie importu:", style="cyan")
        self.console.print(f"▪️ Liczba wszystkich przetworzonych węzłów: [bold cyan]{processed_count}[/bold cyan]")
        self.console.print(f"▪️ Dodano [bold green]{total_added}[/bold green] nowych węzłów menu")
        self.console.print(f"▪️ Zaktualizowano [bold cyan]{total_existed}[/bold cyan] istniejących węzłów")
        self.console.print(f"▪️ Import nie powiódł się dla [bold red]{failure_count}[/bold red] węzłów")
        self.console.print(f"Całkowity czas wykonania operacji wyniósł [bold green]{total_elapsed_time:.2f}[/bold green] sekundy", style="cyan")

    def sort_categories_by_hierarchy(self, all_categories_transformed):
        tree = {}
        for category in all_categories_transformed:
            path = category['category_xpath'].split('\\')
            current_level = tree
            for part in path:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
            current_level['_self'] = category
        def flatten_tree(current_level):
            for name, subtree in current_level.items():
                if name == '_self':
                    yield subtree
                else:
                    yield from flatten_tree(subtree)
        return list(flatten_tree(tree))
      
    def load_menu_cache(self, cache_file):
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as file:
                return json.load(file)
        return {}

    def save_menu_cache(self, cache_file, menu_cache):
        with open(cache_file, 'w') as file:
            json.dump(menu_cache, file, indent=4)
            
    def normalize_filename(self, filename):
        return re.sub(r'[^\w\-_.]', '_', filename)

    async def add_single_category(self, category_data, shop_id, menu_id, custom_lang_id, category_mapping):
        category_path_elements = category_data['category_xpath'].split('\\')
        parent_xpath = '\\'.join(category_path_elements[:-1])
        parent_id = category_mapping.get(parent_xpath, "0")
        translations = category_data.get('translations', None)
        if translations:
            lang_codes = [code for code in translations.keys()]
        else:
            lang_codes = [custom_lang_id if custom_lang_id else 'pol']
        
        lang_data = []
        for lang_code in lang_codes:
            full_lang_code = custom_lang_id if custom_lang_id else convert_lang_codes(lang_code)
            if translations:
                lang_specific_data = translations[lang_code]
            else:
                lang_specific_data = category_data
            lang_data.append({
                "lang_id": full_lang_code,
                "name": lang_specific_data.get('name', ''),
                "priority": lang_specific_data.get('priority', 1),
                "description": lang_specific_data.get('description', ''),
                "item_type": lang_specific_data.get('item_type', ''),
                "meta_title": lang_specific_data.get('meta_title', ''),
                "meta_description": lang_specific_data.get('meta_description', ''),
                "meta_keywords": lang_specific_data.get('meta_keywords', ''),
                "href_target": "_self",
                "hidden": "n",
                "url": lang_specific_data.get('url', '')
            })
        
        payload = {
            "settings": {"textid_separator": "\\"},
            "menu_list": [
                {
                    "shop_id": shop_id,
                    "menu_id": menu_id,
                    "parent_id": parent_id,
                    "lang_data": lang_data
                }
            ]
        }
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "X-API-KEY": self.idosell_api_key
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.idosell_api_menu_gate_url, json=payload, headers=headers)
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data['result'][0].get('faultCode') == 0:
                        new_category_id = response_data['result'][0].get('item_id')
                        return True, new_category_id
                    elif response_data['result'][0].get('faultCode') == 6:
                        existing_category_id = await self.extract_menu_id_from_error(category_data['category_xpath'], shop_id, menu_id, custom_lang_id)
                        if existing_category_id:
                            category_mapping[category_data['category_xpath']] = existing_category_id
                            return True, existing_category_id
                        else:
                            return False, None
                    else:
                        #self.console.print(f"Błąd podczas dodawania kategorii: {response_data.get('error_message', 'Brak szczegółów błędu')}", style="bold red")
                        return False, None
                else:
                    #self.console.print(f"Błąd podczas dodawania kategorii: {response.text}", style="bold red")
                    return False, None
        except Exception as e:
            self.console.print(f"Wystąpił wyjątek: {e}", style="bold red")
            return False, None

    async def extract_menu_id_from_error(self, item_textid, shop_id, menu_id, custom_lang_id):
            # Sprawdzenie, czy drzewo menu jest już w cache'u
            if self.menu_cache is None:
                params = {
                    "shop_id": shop_id,
                    "menu_id": menu_id,
                    "lang_id": custom_lang_id
                }
                headers = {
                    "accept": "application/json",
                    "content-type": "application/json",
                    "X-API-KEY": self.idosell_api_key
                }

                async with httpx.AsyncClient() as client:
                    response = await client.get(self.idosell_api_menu_gate_url, params=params, headers=headers)

                    if response.status_code == 200:
                        try:
                            data = response.json()
                            self.menu_cache = data  # Zapisanie danych do cache'a
                            
                            # Zapisz cache do pliku JSON
                            dir_path = os.getcwd()
                            file_path = os.path.join(self.output_data_folder_for_menu, 'menu_cache.json')
                            with open(file_path, 'w', encoding='utf-8') as file:
                                json.dump(self.menu_cache, file, ensure_ascii=False, indent=4)                        
                            
                        except ValueError:
                            print("Odpowiedź nie jest prawidłowym JSONem. Oto surowa odpowiedź:")
                            print(response.text)
                    else:
                        print("Odpowiedź nie jest prawidłowa. Oto surowa odpowiedź:")
                        print(response.text)

            # Użycie danych z cache'a do wyszukania ID
            for item in self.menu_cache.get('result', []):
                for lang_item in item.get('lang_data', []):
                    if lang_item.get('item_textid') == item_textid:
                        return item.get('item_id')

            return None