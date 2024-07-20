import os
import re
import hashlib
from urllib.parse import urlparse, urljoin
import httpx
import aiofiles

class ImageProcessor:
    def __init__(self, config):
        self.config = config
        self.base_api_url = f"https://{config.WOOCOMMERCE_API_DOMAIN}"
        self.http_client = httpx.AsyncClient()

    async def process_images_in_description(self, description, client, is_product=False):
        # Znajdź wszystkie tagi img z src lub data-src
        image_tags = re.findall(r'<img[^>]+(?:src|data-src)=["\'](.*?)["\']', description)
        updated_description = description

        for original_url in image_tags:
            url = original_url
            # Sprawdzamy, czy URL jest względny (nie zawiera schematu http:// lub https://)
            if not urlparse(url).scheme:
                # Jeśli URL zaczyna się od "/", dodajemy tylko domenę
                if url.startswith('/'):
                    url = f"https://{self.config.WOOCOMMERCE_API_DOMAIN}{url}"
                # W przeciwnym razie dodajemy pełny base_api_url
                else:
                    url = urljoin(self.base_api_url, url)
            
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    image_path = await self.save_image(response.content, urlparse(url).path, is_product)
                    new_path = f'/data/include/cms/description/{image_path}'
                    # Zastąp wszystkie wystąpienia oryginalnego URL nową ścieżką
                    updated_description = updated_description.replace(f'src="{original_url}"', f'src="{new_path}"')
                    updated_description = updated_description.replace(f"src='{original_url}'", f"src='{new_path}'")
                    updated_description = updated_description.replace(f'data-src="{original_url}"', f'data-src="{new_path}"')
                    updated_description = updated_description.replace(f"data-src='{original_url}'", f"data-src='{new_path}'")
                else:
                    print(f"Failed to fetch image (status code {response.status_code}): {url}")
            except httpx.RequestError as e:
                print(f"Failed to fetch image: {url}. Error: {str(e)}")

        return updated_description

    async def save_image(self, image_data, image_url_path, is_product):
        hash_digest = hashlib.md5(image_data).hexdigest()
        image_path_parts = image_url_path.strip('/').split('/')
        normalized_image_name = self.normalize_filename(image_path_parts[-1])
        
        if is_product:
            output_folder = self.config.OUTPUT_IMG_FOLDER_FOR_PRODUCTS
        else:
            output_folder = self.config.OUTPUT_IMG_FOLDER_FOR_CATEGORIES
        
        image_dir = os.path.join(output_folder, *image_path_parts[:-1])
        os.makedirs(image_dir, exist_ok=True)
        full_image_path = os.path.join(image_dir, normalized_image_name)
        
        if not await self.image_already_saved(hash_digest, image_dir):
            async with aiofiles.open(full_image_path, 'wb') as f:
                await f.write(image_data)
        
        return f'{"/".join(image_path_parts[:-1])}/{normalized_image_name}'

    async def image_already_saved(self, hash_digest, directory):
        hash_file = os.path.join(directory, 'hashes.txt')
        if os.path.exists(hash_file):
            async with aiofiles.open(hash_file, 'r') as f:
                content = await f.read()
                if hash_digest in content:
                    return True
        async with aiofiles.open(hash_file, 'a') as f:
            await f.write(hash_digest + '\n')
        return False

    def normalize_filename(self, filename):
        normalized_name = re.sub(r'[^\w\-_.]', '_', filename)
        return normalized_name

    async def close(self):
        await self.http_client.aclose()
