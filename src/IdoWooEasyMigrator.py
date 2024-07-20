


# from modules.categories_api import CategoriesAPI
# from modules.import_product_categories import ImportProductCategories
# from modules.import_navigation_menu import ImportNavigationMenu

import sys
import os
import importlib
import platform
import asyncio
import httpx
import json
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.box import ASCII2
from rich.text import Text
from rich import box
from rich.style import Style

from modules.config_helper import ConfigHelper
from modules.oauth_helper import OAuthHelper
from modules.product_categories_download_helper import CategoriesDownloadHelper
from modules.product_categories_processing_helper import ProductCategoriesProcessingHelper
from modules.product_categories_export_helper import ProductCategoriesExportHelper
from modules.product_categories_import_helper import ProductCategoriesImportHelper
from modules.product_navigations_import import ProductNavigationsImport


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
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
    return ConfigHelper(config_path)
 
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
    async with httpx.AsyncClient() as session:
        if opcja_operacji == "1":
            product_categories_downloader = CategoriesDownloadHelper(session=session, config=config)
            endpoint = product_categories_downloader.wybor_trybu_pobierania_kategorii()
            all_categories = await product_categories_downloader.pobieranie_wszystkich_kategorii(endpoint)
            
            # DEBUG
            # console.print(f"Pobrano {len(all_categories)} kategorii produktów.")        
            
            # Tworzenie instancji ProcessoraCategoriesProcessor
            processor = ProductCategoriesProcessingHelper(all_categories, config.WOOCOMMERCE_API_DOMAIN, config.WOOCOMMERCE_ALIAS_PRODUCT_CATEGORY, config)

            # Przetwarzanie kategorii
            all_categories_process = await processor.process_categories()       
            
            # Transformacja kategorii
            all_categories_transformed = processor.transform_categories()
            
            # Eksport kategorii
            exporter = ProductCategoriesExportHelper(config)
            exporter.export_categories(all_categories, all_categories_process, all_categories_transformed)
            
            if all_categories:
                
                # -------------------------------------------------------- #
                # Pytanie o import kategorii jako kategorie towarów panelu #
                # -------------------------------------------------------- #
                console.print()
                console.print("[black on yellow] Czy chcesz zaimportować pobrane kategorie do panelu jako [bold]\"Kategorie towarów w panelu\"[/bold]? [/black on yellow]", end=" ")
                # Zebranie odpowiedzi z obsługą różnych wariantów dla TRUE i FALSE
                odpowiedz_import_kategorii = input("(Tak/Nie): ").lower()
                true_values = ['t', 'tak', 'y', '1', 'yes']
                false_values = ['n', 'nie', '0', 'no']

                # Sprawdzenie, jaka odpowiedź została podana i odpowiednie formatowanie wyjścia
                if odpowiedz_import_kategorii in true_values:
                    formatted_response = "Tak"
                elif odpowiedz_import_kategorii in false_values:
                    formatted_response = "Nie"
                else:
                    formatted_response = "Nieznana odpowiedź"
                    console.print("Nieprawidłowa odpowiedź. Proszę spróbować ponownie.", style="bold red")
                    # Możesz dodać tutaj logikę ponownego pytania lub wyjścia z funkcji

                console.print(f"[black on green] Wybrano [/black on green] : {formatted_response}\n")

                if odpowiedz_import_kategorii in true_values:
                    # Tworzymy instancję Config z odpowiednią ścieżką do pliku konfiguracyjnego
                    CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
                    config = ConfigHelper(CONFIG_FILE_PATH)
                    
                    # Tworzymy instancję ProductCategoriesImport
                    importer = ProductCategoriesImportHelper(config, config.IDOSELL_API_KEY)
                    
                    # Wywołujemy metodę importu kategorii
                    await importer.import_categories_into_idosell_as_product_categories_in_the_panel(all_categories_transformed)
                
                
                # -------------------------------------------------------- # 
                #      Pytanie o import kategorii jako menu navigacji      #
                # -------------------------------------------------------- #        
                
                console.print()
                console.print("[black on yellow] Czy chcesz zaimportować pobrane kategorie do panelu jako [bold]\"Menu i podstrony opisowe w masce\"[/bold]? [/black on yellow]", end=" ")
                    
                # Zebranie odpowiedzi z obsługą różnych wariantów dla TRUE i FALSE
                odpowiedz_import_menu = input("(Tak/Nie): ").lower()
                true_values = ['t', 'tak', 'y', '1']
                false_values = ['n', 'nie', '0']

                # Sprawdzenie, jaka odpowiedź została podana i odpowiednie formatowanie wyjścia
                if odpowiedz_import_menu in true_values:
                    formatted_response = "Tak"
                elif odpowiedz_import_menu in false_values:
                    formatted_response = "Nie"
                else:
                    formatted_response = "Nieznana odpowiedź"
                    console.print("Nieprawidłowa odpowiedź. Proszę spróbować ponownie.", style="bold red")
                    # Możesz dodać tutaj logikę ponownego pytania lub wyjścia z funkcji

                console.print(f"[black on green] Wybrano [/black on green] : {formatted_response}\n")

                if odpowiedz_import_menu in true_values:
                    importer = ProductNavigationsImport(config)
                    await importer.import_categories_into_idosell_as_navigation_menu_in_shop(all_categories_transformed)

                    console.print()
                    console.print("👊 Kończymy na dziś. Opuszczasz Matrixa. Do zobaczenia wkrótce 👊", style="bold yellow")
                elif odpowiedz_import_menu in false_values:
                    console.print("👊 Kończymy na dziś. Opuszczasz Matrixa. Do zobaczenia wkrótce 👊", style="bold yellow")                            


        elif opcja_operacji == "0":             
            exit()

if __name__ == "__main__":
    asyncio.run(main())