import os
import requests
from tqdm import tqdm

def download_file(url, output_filename):
    if os.path.exists(output_filename):
        print(f"File already exists: {os.path.abspath(output_filename)}")
        print("Skipping download.")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print(f"Starting download: {url}")
    
    with requests.get(url, headers=headers, stream=True) as response:
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024
        
        progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True)
        
        with open(output_filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    file.write(chunk)
                    progress_bar.update(len(chunk))
                    
        progress_bar.close()
    
    print(f"Download complete! Saved as: {os.path.abspath(output_filename)}")
