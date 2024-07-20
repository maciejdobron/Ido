import os
import json

class ConfigHelper:
    def __init__(self, config_file_path):
        with open(config_file_path, 'r') as file:
            config_dict = json.load(file)
        
        # Inicjalizacja atrybutów WooCommerce i IdoSell
        self.WOOCOMMERCE_API_DOMAIN = config_dict["woocommerce_api_domain"]
        self.WOOCOMMERCE_API_CONSUMER_KEY = config_dict["woocommerce_api_consumer_key"]
        self.WOOCOMMERCE_API_CONSUMER_SECRET_KEY = config_dict["woocommerce_api_consumer_secret_key"]
        self.WOOCOMMERCE_API_APPLICATION_PASSWORD = config_dict["woocommerce_api_application_password"]
        self.WOOCOMMERCE_API_USER_LOGIN = config_dict["woocommerce_api_user_login"]
        
        self.WOOCOMMERCE_API_SETTINGS_GATE_URL = f"https://{self.WOOCOMMERCE_API_DOMAIN}/wp-json/wc/v3/settings"
        self.WOOCOMMERCE_API_PRODUCT_GATE_URL = f"https://{self.WOOCOMMERCE_API_DOMAIN}/wp-json/wc/v3/products"
        self.WOOCOMMERCE_API_CATEGORIES_GATE_URL = f"{self.WOOCOMMERCE_API_PRODUCT_GATE_URL}/categories"
        
        self.WOOCOMMERCE_ALIAS_PRODUCT_CATEGORY = config_dict["woocommerce_alias_product_category"]

        # IdoSell API settings
        self.IDOSELL_API_DOMAIN = config_dict["idosell_api_domain"]
        self.IDOSELL_API_KEY = config_dict["idosell_api_key"]
        
        self.IDOSELL_API_PRODUCTS_GATE_URL = f"https://{self.IDOSELL_API_DOMAIN}/api/admin/v3/products/products"
        self.IDOSELL_API_CATEGORIES_GATE_URL = f"https://{self.IDOSELL_API_DOMAIN}/api/admin/v3/products/categories"
        self.IDOSELL_API_MENU_GATE_URL = f"https://{self.IDOSELL_API_DOMAIN}/api/admin/v3/menu/menu"
        self.IDOSELL_API_CUSTOMERS_GATE_URL = f"https://{self.IDOSELL_API_DOMAIN}/api/admin/v3/clients/clients"


        # Inicjalizacja ścieżek katalogów
        self.DIR_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        self.OUTPUT_DATA_FOLDER = os.path.join(self.DIR_PATH, "data", "output")
        self.OUTPUT_DATA_FOLDER_FOR_SETTINGS = os.path.join(self.OUTPUT_DATA_FOLDER, "json", "settings")
        self.OUTPUT_DATA_FOLDER_FOR_CATEGORIES = os.path.join(self.OUTPUT_DATA_FOLDER, "json", "categories")
        self.OUTPUT_DATA_FOLDER_FOR_MENU = os.path.join(self.OUTPUT_DATA_FOLDER, "json", "menu")
        self.OUTPUT_DATA_FOLDER_FOR_PRODUCTS = os.path.join(self.OUTPUT_DATA_FOLDER, "json", "products")
        self.OUTPUT_DATA_FOLDER_FOR_CUSTOMERS = os.path.join(self.OUTPUT_DATA_FOLDER, "json", "customers")
        
        self.OUTPUT_CSV_FOLDER = os.path.join(self.OUTPUT_DATA_FOLDER, "csv")
        self.OUTPUT_CSV_FOLDER_FOR_SETTINGS = os.path.join(self.OUTPUT_CSV_FOLDER, "settings")
        self.OUTPUT_CSV_FOLDER_FOR_CATEGORIES = os.path.join(self.OUTPUT_CSV_FOLDER, "categories")
        self.OUTPUT_CSV_FOLDER_FOR_MENU = os.path.join(self.OUTPUT_CSV_FOLDER, "menu")
        self.OUTPUT_CSV_FOLDER_FOR_PRODUCTS = os.path.join(self.OUTPUT_CSV_FOLDER, "products")
        self.OUTPUT_CSV_FOLDER_FOR_CUSTOMERS = os.path.join(self.OUTPUT_CSV_FOLDER, "customers")  
        
        self.OUTPUT_IMG_FOLDER = os.path.join(self.OUTPUT_DATA_FOLDER, "img")
        self.OUTPUT_IMG_FOLDER_FOR_CATEGORIES = os.path.join(self.OUTPUT_IMG_FOLDER, "categories")
        self.OUTPUT_IMG_FOLDER_FOR_MENU = os.path.join(self.OUTPUT_IMG_FOLDER, "menu")
        self.OUTPUT_IMG_FOLDER_FOR_PRODUCTS = os.path.join(self.OUTPUT_IMG_FOLDER, "products")              
        
        self.OUTPUT_LOGS_FOLDER = os.path.join(self.DIR_PATH, "logs")
        self.OUTPUT_LOGS_FOLDER_FOR_SETTINGS = os.path.join(self.OUTPUT_LOGS_FOLDER, "settings")
        self.OUTPUT_LOGS_FOLDER_FOR_CATEGORIES = os.path.join(self.OUTPUT_LOGS_FOLDER, "categories")
        self.OUTPUT_LOGS_FOLDER_FOR_MENU = os.path.join(self.OUTPUT_LOGS_FOLDER, "menu")
        self.OUTPUT_LOGS_FOLDER_FOR_PRODUCTS = os.path.join(self.OUTPUT_LOGS_FOLDER, "products")
        self.OUTPUT_LOGS_FOLDER_FOR_CUSTOMERS = os.path.join(self.OUTPUT_LOGS_FOLDER, "customers")

        self.SUPPORTED_LANGUAGES = config_dict.get('supported_languages', ['pl', 'en'])

        # Teraz, gdy wszystkie atrybuty są zainicjalizowane, możemy utworzyć katalogi
        self.create_directories()

    def create_directories(self):
        directories = [
            self.OUTPUT_DATA_FOLDER, self.OUTPUT_DATA_FOLDER_FOR_SETTINGS, self.OUTPUT_DATA_FOLDER_FOR_CATEGORIES,
            self.OUTPUT_DATA_FOLDER_FOR_MENU, self.OUTPUT_DATA_FOLDER_FOR_PRODUCTS, self.OUTPUT_DATA_FOLDER_FOR_CUSTOMERS,
            self.OUTPUT_CSV_FOLDER, self.OUTPUT_CSV_FOLDER_FOR_SETTINGS, self.OUTPUT_CSV_FOLDER_FOR_CATEGORIES,
            self.OUTPUT_CSV_FOLDER_FOR_MENU, self.OUTPUT_CSV_FOLDER_FOR_PRODUCTS, self.OUTPUT_CSV_FOLDER_FOR_CUSTOMERS,
            self.OUTPUT_IMG_FOLDER, self.OUTPUT_IMG_FOLDER_FOR_CATEGORIES, self.OUTPUT_IMG_FOLDER_FOR_MENU, self.OUTPUT_IMG_FOLDER_FOR_PRODUCTS,         
            self.OUTPUT_LOGS_FOLDER, self.OUTPUT_LOGS_FOLDER_FOR_SETTINGS, self.OUTPUT_LOGS_FOLDER_FOR_CATEGORIES,
            self.OUTPUT_LOGS_FOLDER_FOR_MENU, self.OUTPUT_LOGS_FOLDER_FOR_PRODUCTS, self.OUTPUT_LOGS_FOLDER_FOR_CUSTOMERS,

        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)            