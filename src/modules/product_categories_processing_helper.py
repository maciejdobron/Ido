# product_categories_processor.py

import os
import copy
import json
import httpx
from typing import List, Dict, Any
from .downloading_graphics_from_descriptions_helper import ImageProcessor

class ProductCategoriesProcessingHelper:
    def __init__(self, all_categories, woocommerce_api_domain, woocommerce_alias_product_category, config):
        self.all_categories = all_categories
        self.woocommerce_api_domain = woocommerce_api_domain
        self.woocommerce_alias_product_category = woocommerce_alias_product_category
        self.config = config
        self.all_categories_process = []
        self.image_processor = ImageProcessor(config)
        self.excluded_attributes = self.load_excluded_attributes()

    async def process_categories(self):
        self.all_categories_process = copy.deepcopy(self.all_categories)
        self.all_categories_process = self.sort_and_group_by_hierarchy(self.all_categories_process)
        await self.process_images_in_categories()
        self.build_category_xpath(self.all_categories_process)
        self.build_parent_names(self.all_categories_process)
        self.build_parent_slugs(self.all_categories_process)
        self.build_parent_xpath(self.all_categories_process)        
        self.build_url_links(self.all_categories_process)
        self.build_item_type(self.all_categories_process)
        self.all_categories_process = [self.exclude_category_attributes(category) for category in self.all_categories_process]
        return self.all_categories_process

    async def process_images_in_categories(self):
        async with httpx.AsyncClient() as client:
            for category in self.all_categories_process:
                if 'description' in category:
                    category['description_with_img'] = await self.image_processor.process_images_in_description(
                        category['description'], 
                        client, 
                        is_product=False
                    )
                    
    def sort_and_group_by_hierarchy(self, categories):
        categories_by_parent = {0: []}
        for category in categories:
            parent_id = category.get('parent', 0)
            if parent_id not in categories_by_parent:
                categories_by_parent[parent_id] = []
            categories_by_parent[parent_id].append(category)

        def sort_categories_by_hierarchy(categories_by_parent):
            sorted_list = []
            parent_categories = sorted(categories_by_parent.get(0, []), key=lambda x: -int(x['id']))

            def sort_children(parent_id, sorted_list):
                if parent_id in categories_by_parent:
                    children_sorted = sorted(categories_by_parent[parent_id], key=lambda x: int(x['id']))
                    for child in children_sorted:
                        sorted_list.append(child)
                        sort_children(child['id'], sorted_list)

            for parent in parent_categories:
                sorted_list.append(parent)
                sort_children(parent['id'], sorted_list)
            return sorted_list

        return sort_categories_by_hierarchy(categories_by_parent)

    def build_category_xpath(self, all_categories):
        """
        Buduje ścieżki XPath dla kategorii.

        :param all_categories: Lista wszystkich kategorii.
        """
        items_by_id = {item['id']: item for item in all_categories}

        for item in all_categories:
            path_parts = []
            current_item = item
            while current_item:
                path_parts.append(current_item['name'])
                parent_id = current_item.get('parent')
                current_item = items_by_id.get(parent_id) if parent_id else None

            # Odwraca ścieżkę, aby zaczynała się od korzenia do liścia
            item['category_xpath'] = '\\'.join(reversed(path_parts))        
        
    def build_parent_names(self, all_categories):
        """
        Przypisuje nazwy rodziców do kategorii.

        :param all_categories: Lista wszystkich kategorii.
        """
        # Tworzenie słownika z identyfikatorami kategorii jako kluczami i kategoriami jako wartościami
        items_by_id = {item['id']: item for item in all_categories}

        for item in all_categories:
            # Dodanie nazwy rodzica do głównej kategorii
            parent_id = item.get('parent')
            item['parent_name'] = items_by_id[parent_id]['name'] if parent_id in items_by_id else ''   
        
    def build_parent_slugs(self, all_categories):
        """
        Przypisuje pełne ścieżki slugów rodziców do kategorii.

        :param all_categories: Lista wszystkich kategorii.
        """
        items_by_id = {item['id']: item for item in all_categories}

        def get_full_parent_slug(category):
            """
            Rekurencyjnie buduje pełną ścieżkę slugów od korzenia do rodzica danej kategorii.

            :param category: Kategoria, dla której budowana jest ścieżka rodziców.
            :return: Pełna ścieżka slugów rodziców.
            """
            parent_id = category.get('parent')
            if not parent_id:
                return ''
            parent_category = items_by_id.get(parent_id)
            parent_slug = get_full_parent_slug(parent_category)
            return f"{parent_slug}/{parent_category['slug']}" if parent_slug else parent_category['slug']

        for item in all_categories:
            # Budowanie pełnej ścieżki slugów dla rodziców każdej kategorii
            item['parent_slug'] = get_full_parent_slug(item)

    def build_parent_xpath(self, all_categories):
        """
        Buduje ścieżki XPath dla rodziców każdej kategorii.

        :param all_categories: Lista wszystkich kategorii.
        """
        items_by_id = {item['id']: item for item in all_categories}

        def get_parent_xpath(category):
            """
            Rekurencyjnie buduje ścieżkę XPath od najwyższego poziomu rodzica do bezpośredniego rodzica danej kategorii.

            :param category: Kategoria, dla której budowana jest ścieżka rodziców.
            :return: Ścieżka XPath rodziców.
            """
            parent_id = category.get('parent')
            if not parent_id:
                return ''
            parent_category = items_by_id.get(parent_id)
            parent_xpath = get_parent_xpath(parent_category)
            return f"{parent_xpath}\\{parent_category['name']}" if parent_xpath else parent_category['name']

        for item in all_categories:
            # Budowanie pełnej ścieżki XPath dla rodziców każdej kategorii
            item['parent_xpath'] = get_parent_xpath(item)
               
    def build_url_links(self, all_categories):
        """
        Buduje pełne linki URL dla każdej kategorii.

        :param all_categories: Lista wszystkich kategorii.
        """
        for item in all_categories:
            segments = [self.woocommerce_api_domain, self.woocommerce_alias_product_category]
            parent_slug = item.get('parent_slug')
            slug = item.get('slug')

            # Dodawanie parent_slug i slug do URL, jeśli nie są puste
            if parent_slug:
                segments.append(parent_slug)
            if slug:
                segments.append(slug)

            # Budowanie pełnego URL na podstawie wcześniej zdefiniowanych elementów
            item['link'] = f"https://{'/'.join(filter(None, segments))}"   
            
    def build_item_type(self, all_categories):
        """
        Modyfikuje pole 'display' dla każdej kategorii na podstawie jej opisu.

        :param all_categories: Lista wszystkich kategorii.
        """
        for category in all_categories:
            display = category.get('display', '')
            description = category.get('description', '')

            # Modyfikowanie wartości display dla głównej kategorii
            if display in ['default', 'products']:
                category['display'] = 'products_with_rich_text' if description else 'products'
            elif display in ['subcategories', 'both']:
                category['display'] = 'navigation_with_rich_text' if description else 'navigation'            
          
    def load_excluded_attributes(self):
        """
        Ładuje atrybuty wykluczone z pliku JSON.
        """
        dir_path = os.getcwd()
        excluded_attributes_path = os.path.join(dir_path, 'data', 'output', 'json', 'categories', 'exclude_category_attributes.json')
       
        try:
            with open(excluded_attributes_path, 'r') as file:
                excluded_attributes = json.load(file)
            return excluded_attributes
        except FileNotFoundError:
            print(f"Plik {excluded_attributes_path} nie został znaleziony. Używam pustego słownika.")
            return {}
        except json.JSONDecodeError:
            print(f"Plik {excluded_attributes_path} zawiera niepoprawny format JSON. Używam pustego słownika.")
            return {}

    def exclude_category_attributes(self, category_data):
        """
        Usuwa określone atrybuty z danych kategorii na podstawie zdefiniowanych reguł.
        Ta funkcja przetwarza dane kategorii, usuwając niechciane atrybuty zgodnie z regułami
        zdefiniowanymi w EXCLUDED_CATEGORIES_ATTRIBUTES. Obsługuje zarówno płaskie jak i zagnieżdżone struktury danych.
        Args:
            category_data (dict): Dane kategorii do przetworzenia.
        Returns:
            dict: Oczyszczone dane kategorii.
        """          
        if not hasattr(self, 'excluded_attributes') or not self.excluded_attributes:
            print("Ostrzeżenie: excluded_attributes nie jest zdefiniowane lub jest puste.")
            return category_data

        def exclude_attributes(data, excluded_info):
            """
            Pomocnicza funkcja do usuwania atrybutów z listy lub słownika.
            Args:
                data (list or dict): Dane do przetworzenia.
                excluded_info (dict or list): Informacje o atrybutach do usunięcia.
            Returns:
                list or dict: Oczyszczone dane.
            """            
       
            if isinstance(data, list):
                # Usuwanie elementów listy na podstawie indeksów
                if 'delete_item_index' in excluded_info:
                    indices_to_delete = excluded_info['delete_item_index']
                    if isinstance(indices_to_delete, int):
                        indices_to_delete = [indices_to_delete]
                    remaining_items = [item for i, item in enumerate(data) if i not in indices_to_delete]
                    # Usuwanie atrybutów z pozostałych elementów listy
                    if 'exclude_attributes' in excluded_info:
                        for item in remaining_items:
                            for excluded_key in excluded_info['exclude_attributes']:
                                item.pop(excluded_key, None)
                    return remaining_items
            elif isinstance(data, dict):
                # Usuwanie atrybutów z obiektów słownikowych
                if isinstance(excluded_info, list):  # Sprawdzenie, czy excluded_info to lista
                    for excluded_key in excluded_info:
                        data.pop(excluded_key, None)
            return data

        # Usuwanie ogólnych atrybutów
        cleaned_category_data = {key: value for key, value in category_data.items() if key not in self.excluded_attributes.get('general', [])}
       
        # Usuwanie zagnieżdżonych atrybutów
        for key, excluded_info in self.excluded_attributes.items():
            if key != 'general':
                key_parts = key.split('.')
                sub_data = category_data
                try:
                    # Iteracja przez zagnieżdżone klucze, z wyjątkiem ostatniego
                    for part in key_parts[:-1]:
                        sub_data = sub_data[part]
                    last_key = key_parts[-1]
                    sub_data[last_key] = exclude_attributes(sub_data[last_key], excluded_info)
                except (KeyError, IndexError):
                    pass
       
        return cleaned_category_data

    def transform_categories(self):
        return [self.transform_category(category) for category in self.all_categories_process]

    def transform_category(self, category):
        """
        Transformuje dane kategorii, tworząc nową strukturę zawierającą przetworzone atrybuty SEO,
        informacje o rodzicu, ścieżki XPath oraz URL-e.

        :param category: Słownik z danymi kategorii do przetworzenia.
        :return: Przekształcony słownik z nowymi nazwami atrybutów.
        """        
        image = category.get("image") or {}
        category_image = image.get("src") if image else ""

        category_seo_title = category.get("yoast_head_json", {}).get('title') or ''
        category_seo_description = category.get("yoast_head_json", {}).get('description') or category.get("yoast_head_json", {}).get('og_description', '') or ''
        category_robots_index = category.get("yoast_head_json", {}).get('robots', {}).get('index') or ''
        category_robots_follow = category.get("yoast_head_json", {}).get('robots', {}).get('follow') or ''

        transformed = {
            "category_id": category.get("id"),
            "category_name": category.get("name"),
            "category_slug": category.get("slug"),
            "category_xpath": category.get("category_xpath"),            
            "parent_id": category.get("parent"),
            "parent_name": category.get("parent_name"),
            "parent_slug": category.get("parent_slug"),
            "parent_xpath": category.get("parent_xpath"),            
            "description": category.get("description_with_img"),
            "item_type": category.get("display"),
            "priority": 1 if category.get("menu_order") == 0 else category.get("menu_order"),
            "category_image": category_image,
            "category_seo_title": category_seo_title,
            "category_seo_description": category_seo_description,
            "category_seo_keywords": '',
            "category_robots_index": category_robots_index,
            "category_robots_follow": category_robots_follow,
            "lang": category.get("lang", "pl"),
            "base_slug": category.get("base", ""),
            "products_count": category.get("count"),
            "category_url": category.get("link")
        }
        return transformed
    
    async def close(self):
        await self.image_processor.close()    