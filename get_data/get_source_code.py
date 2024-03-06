import json
import requests
import time
import shared
shared.init()


def get_source_code(token_address, out_path, retry=0):
    """
    Obtains token source code/abi and saves in json format.

    Parameters
    ----------
    token_address: str
        token address in checksum format.
    out_path : str
        Path to output directory.
    """

    source_code_endpoint = "https://api.etherscan.io/api?" \
                           "module=contract" \
                           "&action=getsourcecode" \
                           f"&address={token_address}" \
                           f"&apikey={shared.API_KEY}"
    try:
        source_code = json.loads(requests.get(source_code_endpoint).text)['result']
    except Exception as e:
        print("connection errors. waiting")
        print(e)
        if retry > 5:
            print("Max retries reached. Skipping")
            return
        get_source_code(token_address, out_path, retry=retry+1)
        # time.sleep(60)
        return

    with open(f"{out_path}/{token_address}.json", "w") as outfile:
        json.dump(source_code, outfile)
    outfile.close()
