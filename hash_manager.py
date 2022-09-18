import hashlib

import requests
from bs4 import BeautifulSoup


class Hash:
    def __init__(self, *args, **kwargs):
        pass
    
    def get_new_hash(self, data):
        url = data['data']['url']
        headers = data['data']['headers']
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "lxml")

        for script in soup(["script", "style"]):
            script.extract()
            soup = soup.get_text()
        
        hash = hashlib.sha224(soup.encode("utf-8")).hexdigest()

        print(f'Scraping generated following hash : {hash}')
        return hash
    
    

