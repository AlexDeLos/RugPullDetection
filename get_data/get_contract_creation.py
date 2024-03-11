from bs4 import BeautifulSoup
import requests
import random


def get_contract_creation(token_address):
    """
    Gets token tx creation hash via web scrapping.

    Parameters
    ----------
    token_address: str
        string corresponding to token address

    Returns
    -------
        tx_creation hash if success, "Not found" otherwise.
    """

    tx_hash_creation = "Not found"
    user_agents_list = [
    'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36',
    ]
    HEADERS = {
        "User-Agent": random.choice(user_agents_list),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    r = requests.get(f'https://etherscan.io/address/{token_address}', headers=HEADERS)
    if r.status_code == 403:
        return "Blocked by Etherscan, try again later."
    elif r.status_code != 200:
        return "something when wrong with the request." + str(r.status_code)
    soup = BeautifulSoup(r.content, 'html.parser')
    soup2 = soup.find_all('a')
    for element in soup2:
        try:
            title = element.get('title')
           
            if title == 'Creator Txn Hash':
                tx_hash_creation = element.get_text()
        except KeyError:
            pass
    if tx_hash_creation != "Not found":
        return tx_hash_creation
    return "Not found"


