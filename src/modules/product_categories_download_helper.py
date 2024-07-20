import asyncio
import httpx
import sys
import os
import json
import traceback
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.box import ASCII2
from rich.text import Text
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from .config_helper import ConfigHelper
from .oauth_helper import OAuthHelper
from .downloading_graphics_from_descriptions_helper import ImageProcessor

class CategoriesDownloadHelper:
    def __init__(self, session: httpx.AsyncClient, config: ConfigHelper):
        self.session = session
        self.config = config
        self.config.create_directories()
        self.oauth_helper = OAuthHelper()
        self.max_per_page = 100
        self.batch_size = 50
        
        # Inicjalizacja ImageProcessor z odpowiednimi argumentami
        base_api_url = config.WOOCOMMERCE_API_DOMAIN if config.WOOCOMMERCE_API_DOMAIN.startswith('http') else f"https://{config.WOOCOMMERCE_API_DOMAIN}"
        dir_path = config.DIR_PATH  # główny katalog projektu
        self.image_processor = ImageProcessor(config)  
        
        # Dodaj właściwość ścieżki do pliku
        self.excluded_attributes_path = os.path.join(dir_path, 'data', 'output', 'json', 'categories', 'exclude_category_attributes.json')
        
        # DEBUG
        print(f"Konstruktor: Przed załadowaniem wykluczonych atrybutów")
        self.excluded_attributes = self.load_excluded_attributes()  
        # DEBUG
        print(f"Załadowane wykluczone atrybuty: {self.excluded_attributes}")

    def wybor_trybu_pobierania_kategorii(self):
        console = Console()

        def custom_prompt():
            prompt_text = "[black on yellow] Podaj numer trybu [/black on yellow] "
            while True:
                opcja = Prompt.ask(prompt_text)
                if opcja.isdigit() and 0 <= int(opcja) <= 4:
                    return int(opcja)
                else:
                    console.print("▣ Nieprawidłowy wybór, spróbuj ponownie:exclamation:\n", style="bold red")

        operacje = {
            1: "Wszystkie kategorie",
            2: "Wszystkie kategorie, z pominięciem tych o podanych identyfikatorach",
            3: "Wybrane kategorie, na podstawie podanych identyfikatorów",
            4: "Wybraną kategorię, do której przypisany jest towar o podanym identyfikatorze",
            0: "Wyjdź"
        }

        menu_text = ""
        last_key = list(operacje.keys())[-1]  # Pobierz ostatni klucz w słowniku
        for key, value in operacje.items():
            if key == last_key:
                menu_text += f"[bold yellow]{key}.[/bold yellow] {value}"  # Nie dodawaj \n dla ostatniego elementu
            else:
                menu_text += f"[bold yellow]{key}.[/bold yellow] {value}\n"            

        panel = Panel(menu_text, title="Wybierz odpowiedni tryb z poniższej listy, wprowadzając jego numer i zatwierdzając wybór klawiszem Enter:", title_align='left', subtitle="WDI Team", subtitle_align='right', padding=(0, 1), width=112, box=ASCII2)
        console.print(panel)

        tryb_pobierania_kategorii = custom_prompt()
        nazwa_trybu = operacje.get(tryb_pobierania_kategorii, "Nieznana operacja")  # Pobierz nazwę operacji na podstawie wybranej opcji
    
        console.print(
            f"[black on green] Wybrano [/black on green] : {nazwa_trybu}\n"  # Wyświetl nazwę operacji
        )
            

        if tryb_pobierania_kategorii == 0:
            console.print("👊 Kończymy na dziś. Opuszczasz Matrixa. Do zobaczenia wkrótce 👊", style="bold yellow")
            sys.exit(0)
            
        elif tryb_pobierania_kategorii == 1:
            endpoint = f"{self.config.WOOCOMMERCE_API_CATEGORIES_GATE_URL}?orderby=id&order=asc&per_page={self.max_per_page}"
            
        elif tryb_pobierania_kategorii == 2:
            console.print("[bold cyan]Podaj identyfikatory kategorii do pominięcia, oddzielone przecinkami:[/bold cyan]", end=" ")
            exclude_ids_str = input()
            exclude_ids = exclude_ids_str.split(",")
            # Usunięcie niepotrzebnych spacji przed i po przecinkach, a następnie podział ciągu znaków na listę identyfikatorów.
            exclude_ids = [id.strip() for id in exclude_ids_str.split(",")]
            # Konwersja wprowadzonych wartości na liczby całkowite, przy założeniu, że wszystkie są poprawnymi liczbami.
            self.exclude_ids = [int(id) for id in exclude_ids if id.isdigit()]

            # Aktualizacja self.category_id_str
            self.category_id_str = ",".join(map(str, self.exclude_ids))
            
            endpoint = f"{self.config.WOOCOMMERCE_API_CATEGORIES_GATE_URL}?orderby=id&order=asc&exclude={self.category_id_str}&per_page={self.max_per_page}"
            
        elif tryb_pobierania_kategorii == 3:
            console.print("[bold cyan]Podaj identyfikatory kategorii do pobrania, oddzielone przecinkami:[/bold cyan]", end=" ")
            include_ids_str = input()
            # Usuwamy białe znaki dla każdego identyfikatora oraz dzielimy ciąg na podstawie przecinków.
            include_ids = [id.strip() for id in include_ids_str.split(",")]
            # Filtrujemy i konwertujemy tylko te identyfikatory, które są cyframi.
            self.include_ids = [int(id) for id in include_ids if id.isdigit()]

            # Aktualizacja self.ids_str do przechowywania identyfikatorów jako ciągu znaków oddzielonych przecinkami.
            self.ids_str = ",".join(map(str, self.include_ids))
            
            endpoint = f"{self.config.WOOCOMMERCE_API_CATEGORIES_GATE_URL}?orderby=id&order=asc&include={self.ids_str}&per_page={self.max_per_page}"
            
        elif tryb_pobierania_kategorii == 4:
            console.print("[bold cyan]Podaj identyfikator towaru, dla którego ma być pobrana kategoria:[/bold cyan]", end=" ")
            product_id_str = input()
            self.product_id = int(product_id_str.strip()) if product_id_str.strip().isdigit() else None
            
            endpoint = f"{self.config.WOOCOMMERCE_API_CATEGORIES_GATE_URL}?product={self.product_id}&per_page={self.max_per_page}"
        else:
            console.print("▣ Nieprawidłowy wybór, spróbuj ponownie:exclamation:\n", style="bold red")
            return     
            
        return endpoint

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        retry=retry_if_exception_type((httpx.ReadTimeout, httpx.ConnectError))
    )
    async def obliczanie_liczby_kategorii_i_stron_odpowiedzi_api(self, endpoint):
        console = Console()
        
        status_message = "Obliczanie liczby kategorii do pobrania"
        
        with console.status(f"[bold cyan]{status_message}[/bold cyan]", spinner="dots6", spinner_style="bold cyan", speed=1.0) as status:
            oauth_path = self.oauth_helper.generate_oauth_url("HEAD", endpoint, self.config.WOOCOMMERCE_API_CONSUMER_KEY, self.config.WOOCOMMERCE_API_CONSUMER_SECRET_KEY)
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.head(oauth_path)

                    if response.status_code == 200:
                        x_wp_total = response.headers.get('X-WP-Total')
                        x_wp_totalpages = response.headers.get('X-WP-TotalPages')

                        if x_wp_total is not None and x_wp_totalpages is not None:
                            total_categories = int(x_wp_total)
                            total_categories_pages = int(x_wp_totalpages)
                            
                            strony_text = self.odmien_rzeczownik(total_categories_pages, "strona")
                            kategorie_text = self.odmien_rzeczownik(total_categories, "kategoria")
                            
                            console.print(
                                f"⭐",
                                f"Do pobrania jest łącznie [bold bright_blue]{total_categories}[/bold bright_blue] {kategorie_text},", 
                                f"które zostały podzielone na [bold bright_blue]{total_categories_pages}[/bold bright_blue] {strony_text} odpowiedzi.",
                                style="bold green"
                            )                                                     
                            
                            return total_categories, total_categories_pages
                        else:
                            status.stop()
                            console.print("[bold red]▣[/bold red] Nie znaleziono oczekiwanych nagłówków 'X-WP-Total' i 'X-WP-TotalPages' w odpowiedzi", style="bold red")
                            return None, None
                    else:
                        status.stop()
                        console.print(f"[bold red]▣[/bold red] Status [red]{response.status_code}[/red] : Nie udało się poprawnie połączyć i pobierać nagłówków z [bold cyan]{endpoint}[/bold cyan]", style="bold red")
                        self._display_error_message(error_message)
                        return None, None 
            
            except httpx.ReadTimeout:
                status.stop()
                error_message = "▣ Upłynął limit czasu oczekiwania na odpowiedź serwera. Sprawdź swoje połączenie internetowe i spróbuj ponownie później."
                self._display_error_message(error_message)
                return None, None
            except httpx.ConnectError:
                status.stop()
                error_message = "▣ Nie można nawiązać połączenia z serwerem. Sprawdź swoje połączenie internetowe i upewnij się, że serwer jest dostępny."
                self._display_error_message(error_message)
                return None, None
            except Exception as e:
                status.stop()
                error_message = f"▣ Wystąpił nieoczekiwany błąd: {str(e)}"
                self._display_error_message(error_message)
                return None, None
      
    
    def _display_error_message(self, message):
        console = Console()
        error_panel = Panel(
            Text(message, style="bold red"),
            title="Błąd połączenia",
            title_align='left', 
            subtitle="WDI Team", 
            subtitle_align='right', 
            padding=(0, 1), 
            width=112,
            border_style="red",
            expand=False, 
            box=ASCII2
        )
        console.print(error_panel)    
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        retry=retry_if_exception_type((httpx.ReadTimeout, httpx.ConnectError))
    )
    async def pobieranie_wszystkich_kategorii(self, endpoint):
        console = Console()
        try: 
            total_categories, total_categories_pages = await self.obliczanie_liczby_kategorii_i_stron_odpowiedzi_api(endpoint)      
            if total_categories_pages is None:
                console.print("Nie udało się pobrać informacji o liczbie kategorii.", style="bold red")
                return []        
            
            all_categories = []
            
            page = 1
            while page <= total_categories_pages:
                current_batch_pages = min(self.batch_size, total_categories_pages - page + 1)
                current_batch_pages_start = page
                current_batch_pages_end = page + current_batch_pages - 1
                strony_text2 = self.odmien_rzeczownik(total_categories_pages, "strona2")
                current_page_message = f"[bold cyan]Trwa pobieranie szczegółowych danych dotyczących kategorii z zakresu stron od [bold yellow]{current_batch_pages_start}[/bold yellow] do [bold yellow]{current_batch_pages_end}[/bold yellow] z całkowitej liczby [bold yellow]{total_categories_pages}[/bold yellow] {strony_text2}.[/bold cyan]"  
                
                with console.status(current_page_message, spinner="dots6", spinner_style="bold yellow", speed=1.0):
                    start_time = asyncio.get_event_loop().time()
                    
                    tasks = [self.pobieranie_paczki_z_kategoriami(page + i, endpoint) for i in range(current_batch_pages)]
                    categories_batches = await asyncio.gather(*tasks)
                    
                    batch_categories_count = sum(len(batch) for batch in categories_batches)
                    all_categories.extend([cat for batch in categories_batches for cat in batch])
                    
                    elapsed_time = asyncio.get_event_loop().time() - start_time
                    
                    console.print(
                        f"⭐",
                        f"Przetworzono kategorie ze stron od [bold bright_blue]{current_batch_pages_start}[/bold bright_blue] do [bold bright_blue]{current_batch_pages_end}[/bold bright_blue] z łącznej liczby [bold bright_blue]{total_categories_pages}[/bold bright_blue] {strony_text2}.",
                        f"Uzyskano dane dotyczące [bold bright_blue]{batch_categories_count}[/bold bright_blue] kategorii z łącznej liczby [bold bright_blue]{len(all_categories)}[/bold bright_blue] kategorii (czas wykonania operacji wyniósł [bold bright_blue]{elapsed_time:.2f}[/bold bright_blue] sekundy).",
                        style="bold green"
                    )                   
                    
                    page += current_batch_pages
            
            # Liczenie unikalnych kategorii
            unique_categories = set(cat['id'] for cat in all_categories)
            # console.print(f"Całkowita liczba pobranych unikalnych kategorii: [bold bright_blue]{len(unique_categories)}[/bold bright_blue]")
            
            # Sprawdzenie duplikatów
            if len(unique_categories) != len(all_categories):
                console.print(f"[bold yellow]Uwaga:[/bold yellow] Wykryto [bold red]{len(all_categories) - len(unique_categories)}[/bold red] zduplikowanych kategorii.", style="bold yellow")
                
                # Opcjonalnie: Wyświetl informacje o duplikatach
                category_counts = {}
                for cat in all_categories:
                    category_counts[cat['id']] = category_counts.get(cat['id'], 0) + 1
                duplicates = {id: count for id, count in category_counts.items() if count > 1}
                if duplicates:
                    console.print("Zduplikowane kategorie:")
                    for id, count in duplicates.items():
                        console.print(f"  Kategoria ID {id}: powtórzona {count} razy")

            # Sprawdzenie zgodności z początkowymi danymi
            if total_categories != len(unique_categories):
                console.print(f"[bold yellow]Uwaga:[/bold yellow] Liczba pobranych unikalnych kategorii ([bold red]{len(unique_categories)}[/bold red]) nie zgadza się z początkową liczbą kategorii ([bold red]{total_categories}[/bold red]).", style="bold yellow")

            return all_categories    
        except httpx.ReadTimeout:
            console.print("Wystąpił błąd timeout podczas pobierania kategorii. Spróbuj ponownie później.", style="bold red")
            return []
        except Exception as e:
            console.print(f"Wystąpił nieoczekiwany błąd podczas pobierania kategorii: {str(e)}", style="bold red")
            return []        

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        retry=retry_if_exception_type((httpx.ReadTimeout, httpx.ConnectError))
    )
    async def pobieranie_paczki_z_kategoriami(self, page, endpoint):
        console = Console()
        # Dodajemy parametr page do endpointa
        if '?' in endpoint:
            paginated_endpoint = f"{endpoint}&page={page}"
        else:
            paginated_endpoint = f"{endpoint}?page={page}"
    
        # DEBUG
        # console.log(f"Wywoływany endpoint URL: {paginated_endpoint}")
        oauth_path = OAuthHelper.generate_oauth_url("GET", paginated_endpoint, self.config.WOOCOMMERCE_API_CONSUMER_KEY, self.config.WOOCOMMERCE_API_CONSUMER_SECRET_KEY)
    
        async with httpx.AsyncClient() as client:
            response = await client.get(oauth_path)
            if response.status_code == 200:
                categories_batch = response.json()
            
                # DEBUG
                # console.print(f"Pobrano {len(categories_batch)} kategorii ze strony {page}")
            
                if not categories_batch:
                    return []
                
                return categories_batch
            else:
                console.print(f"Błąd przy pobieraniu kategorii: Status {response.status_code}, Odpowiedź: {response.text}", style="bold red")
                return []

    def odmien_rzeczownik(self, liczba, typ):
        """
        Funkcja odmienia rzeczownik w zależności od podanej liczby i typu rzeczownika.

        Args:
        liczba (int): Liczba, która ma być odmieniona.
        typ (str): Typ rzeczownika, który ma być odmieniony. Może być jednym z:
                   'strona', 'strona2', 'kategoria', 'tlumaczenie'.

        Returns:
        str: Odmieniony rzeczownik w odpowiedniej formie.

        Raises:
        ValueError: Jeśli podano nieznany typ rzeczownika.
        """
        liczba = abs(liczba)  # zabezpieczenie przed liczbami ujemnymi
        ostatnie_dwie_cyfry = liczba % 100
        ostatnia_cyfra = liczba % 10

        if typ == "strona":
            # Odmiana dla rzeczownika "strona"
            if liczba == 1:
                return "stronę"
            elif 11 <= ostatnie_dwie_cyfry <= 19:
                return "stron"
            elif ostatnia_cyfra == 1:
                return "stron"
            elif 2 <= ostatnia_cyfra <= 4:
                return "strony"
            else:
                return "stron"

        elif typ == "strona2":
            # Odmiana dla rzeczownika "strona" w innej formie
            if liczba == 1:
                return "strony"
            else:
                return "stron"

        elif typ == "kategoria":
            # Odmiana dla rzeczownika "kategoria"
            if liczba == 1:
                return "kategoria"
            elif 11 <= ostatnie_dwie_cyfry <= 19:
                return "kategorii"
            elif ostatnia_cyfra == 1:
                return "kategorii"
            elif 2 <= ostatnia_cyfra <= 4 and not (11 <= ostatnie_dwie_cyfry <= 14):
                return "kategorie"
            else:
                return "kategorii"

        elif typ == "tlumaczenie":
            # Odmiana dla rzeczownika "tlumaczenie"
            if liczba == 1:
                return "jednego tłumaczenia"
            else:
                return "tłumaczeń"

        else:
            # Rzucenie wyjątku w przypadku nieznanego typu rzeczownika
            raise ValueError("Nieznany typ rzeczownika")
   
    def load_excluded_attributes(self):
        """
        Ładuje atrybuty wykluczone z pliku JSON.
        """
        print(f"Bieżący katalog roboczy: {os.getcwd()}")  # Dodaj ten wiersz, aby sprawdzić bieżący katalog roboczy
        print(f"Ścieżka do pliku: {self.excluded_attributes_path}")  # Dodaj ten wiersz, aby sprawdzić pełną ścieżkę do pliku
        
        try:
            with open(self.excluded_attributes_path, 'r') as file:
                excluded_attributes = json.load(file)
            return excluded_attributes
        except FileNotFoundError:
            print(f"Plik {self.excluded_attributes_path} nie został znaleziony. Używam pustego słownika.")
            return {}
        except json.JSONDecodeError:
            print(f"Plik {self.excluded_attributes_path} zawiera niepoprawny format JSON. Używam pustego słownika.")
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
