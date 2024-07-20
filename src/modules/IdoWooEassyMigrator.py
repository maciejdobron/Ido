from .config_helper import ConfigHelper
from .oauth_helper import OAuthHelper
from .product_categories_download_helper import CategoriesDownloader
# from modules.categories_api import CategoriesAPI
# from modules.import_product_categories import ImportProductCategories
# from modules.import_navigation_menu import ImportNavigationMenu


import importlib
import platform
import asyncio
import httpx
import os
import json
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.box import ASCII2
from rich.text import Text
from rich import box
from rich.style import Style



# Funkcja do czyszczenia ekranu
def clear_console():
    command = 'cls' if platform.system().lower() == 'windows' else 'clear'
    os.system(command)

def logo_mgi_tools():
    wdi_ascii = """Witaj w Matrixie IdoSell:


           ooo        ooooo   .oooooo.    ooooo      ooooooooooooo                     oooo           
           `88.       .888'  d8P'  `Y8b   `888'      8'   888   `8                     `888           
            888b     d'888  888            888            888       .ooooo.   .ooooo.   888   .oooo.o 
            8 Y88. .P  888  888            888            888      d88' `88b d88' `88b  888  d88(  "8 
            8  `888'   888  888     ooooo  888            888      888   888 888   888  888  `"Y88b.  
            8    Y     888  `88.    .88'   888            888      888   888 888   888  888  o.  )88b 
           o8o        o888o  `Y8bood8P'   o888o          o888o     `Y8bod8P' `Y8bod8P' o888o 8""888P' 
                                                                       vs. 1.0.0.0 by Maciej Dobroń ®
                                                                       
    """   
    return wdi_ascii

def pokaz_menu_wyboru_operacji():
    console = Console()

    def custom_prompt():
        question = "[black on yellow] Podaj numer operacji [/black on yellow] "
        while True:
            response = Prompt.ask(question)
            if response in ["1", "2", "3", "4", "5", "6", "0"]:
                return response
            console.print(":no_entry: Nieprawidłowy wybór, spróbuj ponownie:exclamation:\n", style="bold red")
        
    operacje = {
        "1": "Pobieranie kategorii towarów",
        "2": "Pobieranie menu nawigacji w sklepie",
        "3": "Pobieranie towarów",
        "4": "Pobieranie opinii do towarów",
        "5": "Pobieranie wpisów blogowych",
        "6": "Pobieranie klientów",
        "7": "Pobieranie subskrybentów newslettera (w krótce)",
        "0": "Wyjdź"
    }     
        
    menu_text = ""
    last_key = list(operacje.keys())[-1]  # Pobierz ostatni klucz w słowniku
    for key, value in operacje.items():
        if key == last_key:
            menu_text += f"[bold yellow]{key}.[/bold yellow] {value}"  # Nie dodawaj \n dla ostatniego elementu
        else:
            menu_text += f"[bold yellow]{key}.[/bold yellow] {value}\n"

    panel = Panel(menu_text, title="Wybierz odpowiednią opcję z poniższej listy, wprowadzając jej numer i zatwierdzając wybór klawiszem Enter:", title_align='left', subtitle="MGI Team", subtitle_align='right', safe_box=None, padding=(0, 1), width=110, box=ASCII2)
    console.print(panel)

    opcja_operacji = custom_prompt()
    nazwa_operacji = operacje.get(opcja_operacji, "Nieznana operacja")  # Pobierz nazwę operacji na podstawie wybranej opcji
    
    console.print(
        f"[black on green] Wybrano [/black on green] : {nazwa_operacji}\n"  # Wyświetl nazwę operacji
    )
    
    if opcja_operacji == "0":
        console.print("👊 Kończmy na dziś. Opuszczasz Matrixa. Do zobaczenia wkrótce 👊", style="bold yellow")   
        wykonano_operacje = True   
        
    return opcja_operacji       
 
def load_config():
    with open('config.json', 'r') as config_file:
        config_dict = json.load(config_file)
    return Config(config_dict)
 
async def main():  
    console = Console()
    session = None    
    
    # Wczytanie konfiguracji połączenia
    config = load_config()
     
    #clear_console()
    console.print(logo_mgi_tools())
    console.print("")
    opcja_operacji = pokaz_menu_wyboru_operacji()


# Pobieranie drzewa kategorii z API WooCommerce    
    if opcja_operacji == "1":
        product_categories_downloader = CategoriesDownloader(config)
        all_product_categories = await product_categories_downloader.download_all_categories()
        console.print(f"Pobrano {len(all_product_categories)} kategorii produktów.")        
        
    
        # # -------------------------------------------------------- #
        # # Pytanie o import kategorii jako kategorie towarów panelu #
        # # -------------------------------------------------------- #

        # console.print()
        # console.print("[black on yellow] Czy chcesz zaimportować pobrane kategorie do panelu jako [bold]\"Kategorie towarów w panelu\"[/bold]? [/black on yellow]", end=" ")

        # # Zebranie odpowiedzi z obsługą różnych wariantów dla TRUE i FALSE
        # odpowiedz_import_kategorii = input("(Tak/Nie): ").lower()
        # true_values = ['t', 'tak', 'y', '1', 'yes']
        # false_values = ['n', 'nie', '0', 'no']

        # # Sprawdzenie, jaka odpowiedź została podana i odpowiednie formatowanie wyjścia
        # if odpowiedz_import_kategorii in true_values:
        #     formatted_response = "Tak"
        # elif odpowiedz_import_kategorii in false_values:
        #     formatted_response = "Nie"
        # else:
        #     formatted_response = "Nieznana odpowiedź"
        #     console.print("Nieprawidłowa odpowiedź. Proszę spróbować ponownie.", style="bold red")
        #     # Możesz dodać tutaj logikę ponownego pytania lub wyjścia z funkcji

        # console.print(f"[black on green] Wybrano [/black on green] : {formatted_response}\n")

        # if odpowiedz_import_kategorii in true_values:
        #     # Zakładamy, że mamy dostęp do obiektu config
        #     config = Config()
            
        #     # Tworzymy instancję ImportProductCategories
        #     async with httpx.AsyncClient() as client:
        #         product_categories_instance = ImportProductCategories(
        #             session=client,
        #             config=config
        #         )
                
        #         # Wywołujemy metodę importu kategorii
        #         await product_categories_instance.import_categories_into_idosell(all_categories)
        
        # # -------------------------------------------------------- # 
        # #      Pytanie o import kategorii jako menu navigacji      #
        # # -------------------------------------------------------- #        
        
        # console.print()
        # console.print("[black on yellow] Czy chcesz zaimportować pobrane kategorie do panelu jako [bold]\"Menu i podstrony opisowe w masce\"[/bold]? [/black on yellow]", end=" ")
            
        # # Zebranie odpowiedzi z obsługą różnych wariantów dla TRUE i FALSE
        # odpowiedz_import_menu = input("(Tak/Nie): ").lower()
        # true_values = ['t', 'tak', 'y', '1']
        # false_values = ['n', 'nie', '0']

        # # Sprawdzenie, jaka odpowiedź została podana i odpowiednie formatowanie wyjścia
        # if odpowiedz_import_menu in true_values:
        #     formatted_response = "Tak"
        # elif odpowiedz_import_menu in false_values:
        #     formatted_response = "Nie"
        # else:
        #     formatted_response = "Nieznana odpowiedź"
        #     console.print("Nieprawidłowa odpowiedź. Proszę spróbować ponownie.", style="bold red")
        #     # Możesz dodać tutaj logikę ponownego pytania lub wyjścia z funkcji

        # console.print(f"[black on green] Wybrano [/black on green] : {formatted_response}\n")

        # if odpowiedz_import_menu in true_values:
        #     navigation_menu_instance = ImportNavigationMenu(
        #         session=session,
        #         idosell_api_menu_gate_url=categories_api_instance.idosell_api_menu_gate_url,
        #         idosell_api_key=categories_api_instance.idosell_api_key,                
        #         output_data_folder_for_categories=categories_api_instance.output_data_folder_for_categories,
        #         output_data_folder_for_menu=categories_api_instance.output_data_folder_for_menu,
        #         output_logs_folder_for_menu=categories_api_instance.output_logs_folder_for_menu,                
        #         supported_languages=categories_api_instance.supported_languages
        #     )
        #     await navigation_menu_instance.import_categories_into_idosell_as_navigation_menu_in_shop(all_categories)
        #     console.print()
        #     console.print("👊 Kończymy na dziś. Opuszczasz Matrixa. Do zobaczenia wkrótce 👊", style="bold yellow")
        # elif odpowiedz_import_menu in false_values:
        #     console.print("👊 Kończymy na dziś. Opuszczasz Matrixa. Do zobaczenia wkrótce 👊", style="bold yellow")                            







# Pobieranie drzewa menu z API Wordpress                             
    # elif opcja_operacji == "2": 
    #     MenuAPI = importlib.import_module("MenuAPI").MenuAPI
    #     menu_api_instance = MenuAPI(
    #         session=session,
    #         api_url=api_url,
    #         api_wp_login=api_wp_login, 
    #         api_wp_password=api_wp_password,
    #         idosell_api_domain=idosell_api_domain,
    #         idosell_api_key=idosell_api_key,
    #         idosell_api_menu_url=idosell_api_menu_url
    #     )
        
    #     result = await menu_api_instance.downloading_the_elements_of_the_selected_menu()
        

    #     # Pytanie o import menu do IdoSell
    #     if result:  # Wykonuje tylko, jeśli downloading_the_elements_of_the_selected_menu zwróci True
                
    #         # Wyświetlenie stylizowanego pytania
    #         console.print()
    #         console.print("[black on yellow] Czy chcesz zaimportować pobrane menu do panelu IdoSell?[/black on yellow] ", end="")

    #         # Zebranie odpowiedzi z obsługą różnych wariantów dla TRUE i FALSE
    #         odpowiedz = input("(Tak/Nie): ").lower()
    #         true_values = ['t', 'tak', 'y', '1']
    #         false_values = ['n', 'nie', '0']

    #         # Sprawdzenie, jaka odpowiedź została podana i odpowiednie formatowanie wyjścia
    #         if odpowiedz in true_values:
    #             formatted_response = "Tak"
    #         elif odpowiedz in false_values:
    #             formatted_response = "Nie"
    #         else:
    #             formatted_response = "Nieznana odpowiedź"
    #             console.print("Nieprawidłowa odpowiedź. Proszę spróbować ponownie.", style="bold red")
    #             # Możesz dodać tutaj logikę ponownego pytania lub wyjścia z funkcji

    #         console.print(f"[black on green] Wybrano [/black on green] : {formatted_response}\n")

    #         if odpowiedz in true_values:
    #             nazwa_pliku = os.path.join(dir_path, 'json', 'menu',  'menu_data.json')
    #             await menu_api_instance.importing_menus_into_idosell_panel()
    #         elif odpowiedz in false_values:
    #             console.print("👊 Kończymy na dziś. Opuszczasz Matrixa. Do zobaczenia wkrótce 👊", style="bold yellow")

    # elif opcja_operacji == "3":
    #     ProductsSizesAPI = importlib.import_module("ProductsAPI").ProductsAPI
    #     async with ProductsSizesAPI(
    #         session=session,
    #         api_url=api_url,
    #         consumer_key=consumer_key, 
    #         consumer_secret=consumer_secret,
    #         woocommerce_api_product=woocommerce_api_product,
    #         woocommerce_api_categories=woocommerce_api_categories,
    #         idosell_api_domain=idosell_api_domain,
    #         idosell_api_key=idosell_api_key,
    #         idosell_api_products_url=idosell_api_products_url,
    #         supported_languages=None
    #     ) as products_api_instance:
        
    #         # Budowanie pełnej ścieżki do pliku
    #         config_file_path = os.path.join(dir_path, 'json', 'data', 'wp_config.json')
            
    #         # Sprawdzenie istnienia katalogu i jego utworzenie, jeśli nie istnieje
    #         os.makedirs(os.path.dirname(config_file_path), exist_ok=True)
            
    #         # Sprawdzenie, czy plik konfiguracyjny już istnieje
    #         if not os.path.exists(config_file_path):
    #             await products_api_instance.fetch_and_save_config()        
        
    #         # Budowanie pełnej ścieżki do pliku
    #         categories_file_path = os.path.join(dir_path, 'json', 'data', 'categories_config.json')
            
    #         # Sprawdzenie istnienia katalogu i jego utworzenie, jeśli nie istnieje
    #         os.makedirs(os.path.dirname(categories_file_path), exist_ok=True)
            
    #         # Sprawdzenie, czy plik konfiguracyjny już istnieje
    #         if not os.path.exists(categories_file_path):
    #             await products_api_instance.fetch_all_categories()        
            
    #         products = await products_api_instance.fetch_all_products()

    #         if products is None:
    #             # console.print("[bold red]Brak produktów do przetworzenia.[/bold red]")
    #             return

    #         # Pobieranie wariantów, jeśli są dostępne, ale nie przerywaj, jeśli ich nie ma
    #         products_with_variants = await products_api_instance.fetch_all_variants(products)
            
    #         # Niezależnie od istnienia wariantów, próbuj pobierać tłumaczenia dla produktów
    #         products_with_translations = await products_api_instance.fetch_all_translations(products_with_variants if products_with_variants is not None else products)


    #         # Upewnij się, że mamy produkty do sortowania i zapisu
    #         if products_with_translations is not None:
    #             # Sortowanie produktów po 'id'
    #             products_sorted = sorted(products_with_translations, key=lambda x: x['id'])
                
    #             # Dalsze przetwarzanie...
    #             await products_api_instance.make_data_for_api(products_sorted)
                
    #             # Określenie ścieżki i zapis do pliku JSON3
    #             file_path = os.path.join(dir_path, 'json', 'products', "products.json")

    #             # Sprawdzenie istnienia katalogu i jego utworzenie, jeśli nie istnieje
    #             os.makedirs(os.path.dirname(file_path), exist_ok=True)            
                
    #             with open(file_path, "w", encoding="utf-8") as f:
    #                 json.dump(products_sorted, f, ensure_ascii=False, indent=4)
    #         else:
    #             console.print("[bold red]▣ Brak produktów z tłumaczeniami do zapisu.[/bold red]")               


    #         console.print()
    #         # Pytanie o import kategorii jako menu
    #         console.print("[black on yellow] Czy chcesz zaimportować pobrane towary do panelu IdoSell? [/black on yellow] ", end="")

    #         # Zebranie odpowiedzi z obsługą różnych wariantów dla TRUE i FALSE
    #         odpowiedz3 = input("(Tak/Nie): ").lower()
    #         true_values = ['t', 'tak', 'y', '1']
    #         false_values = ['n', 'nie', '0']

    #         # Sprawdzenie, jaka odpowiedź została podana i odpowiednie formatowanie wyjścia
    #         if odpowiedz3 in true_values:
    #             formatted_response = "Tak"
    #         elif odpowiedz3 in false_values:
    #             formatted_response = "Nie"
    #         else:
    #             formatted_response = "Nieznana odpowiedź"
    #             console.print("▣ Nieprawidłowa odpowiedź. Proszę spróbować ponownie.", style="bold red")
    #             # Możesz dodać tutaj logikę ponownego pytania lub wyjścia z funkcji
               
    #         console.print(f"[black on green] Wybrano [/black on green] : {formatted_response}\n")
            
    #         if odpowiedz3 in true_values:
    #             await products_api_instance.import_products_into_panel_idosell()



    #     # Pytanie o import kategorii jako kategorie towarów panelu
    #     console.print()
    #     console.print("[black on yellow] Czy chcesz zaimportować kategorie do panelu IdoSell jako Kategorie towarów w panelu? [/black on yellow]", end=" ")
        
    #     # Zebranie odpowiedzi z obsługą różnych wariantów dla TRUE i FALSE
    #     odpowiedz4 = input("(Tak/Nie): ").lower()
    #     true_values = ['t', 'tak', 'y', '1']
    #     false_values = ['n', 'nie', '0']

    #     # Sprawdzenie, jaka odpowiedź została podana i odpowiednie formatowanie wyjścia
    #     if odpowiedz4 in true_values:
    #         formatted_response = "Tak"
    #     elif odpowiedz4 in false_values:
    #         formatted_response = "Nie"
    #     else:
    #         formatted_response = "Nieznana odpowiedź"
    #         console.print("Nieprawidłowa odpowiedź. Proszę spróbować ponownie.", style="bold red")
    #         # Możesz dodać tutaj logikę ponownego pytania lub wyjścia z funkcji

    #     console.print(f"[black on green] Wybrano [/black on green] : {formatted_response}\n")

    #     if odpowiedz4 in true_values:
    #         await products_api_instance.group_products_into_panel_idosell()               
    #     elif odpowiedz4 in false_values:
    #         console.print("👊 Kończymy na dziś. Opuszczasz Matrixa. Do zobaczenia wkrótce 👊", style="bold yellow") 
  
    # elif opcja_operacji == "4":             
    #     pass
                
    # elif opcja_operacji == "5":                    
    #     pass           
                
    # elif opcja_operacji == "6":             
    #     CustomersAPI = importlib.import_module("CustomersAPI").CustomersAPI
    #     async with CustomersAPI(
    #         session=session,
    #         api_url=api_url,
    #         consumer_key=consumer_key, 
    #         consumer_secret=consumer_secret
    #     ) as customers_api_instance:
            
    #         file_path = os.path.join(customers_api_instance.json_output_folder_for_customers, 'customers_data.json')
    #         if os.path.exists(file_path):
                
    #             # Pytanie o import kategorii jako kategorie towarów panelu
    #             console.print("[black on yellow] Plik z danymi klientów już istnieje. Czy chcesz kontynuować korzystając z tego pliku? [/black on yellow]", end=" ")
                
    #             # Zebranie odpowiedzi z obsługą różnych wariantów dla TRUE i FALSE
    #             odpowiedz_do_pytania_o_plik = input("(Tak/Nie): ").lower()
    #             true_values = ['t', 'tak', 'y', '1']
    #             false_values = ['n', 'nie', '0']

    #             # Sprawdzenie, jaka odpowiedź została podana i odpowiednie formatowanie wyjścia
    #             if odpowiedz_do_pytania_o_plik in true_values:
    #                 formatted_response = "Tak"
    #             elif odpowiedz_do_pytania_o_plik in false_values:
    #                 formatted_response = "Nie"
    #             else:
    #                 formatted_response = "Nieznana odpowiedź"
    #                 console.print("▣ Nieprawidłowa odpowiedź. Proszę spróbować ponownie.", style="bold red")
    #                 # Możesz dodać tutaj logikę ponownego pytania lub wyjścia z funkcji

    #             console.print(f"[black on green] Wybrano [/black on green] : {formatted_response}\n")

    #             if odpowiedz_do_pytania_o_plik in true_values:
    #                 all_customers = await customers_api_instance.load_customers_from_file(file_path)
    #             else:
    #                 all_customers = await customers_api_instance.fetch_all_customers()
    #                 await customers_api_instance.save_customers_to_file(all_customers)                                     
    #         else:
    #             all_customers = await customers_api_instance.fetch_all_customers()
    #             await customers_api_instance.save_customers_to_file(all_customers)

    #         opcja_customers = await customers_api_instance.show_menu_and_select_customers()
    #         await customers_api_instance.filtered_customers(opcja_customers, all_customers)            
             
    # elif opcja_operacji == "7":             
    #     pass                                

    elif opcja_operacji == "0":             
        exit()

if __name__ == "__main__":
    asyncio.run(main())