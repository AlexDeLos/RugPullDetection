import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
import shared
from Utils.eth_utils import get_logs, events_to_json
shared.init()


def get_pool_events(events_name, hashed_event, pool_address, out_path, start_block, end_block):
    """
    Get pool logs for a given pool and period.
    This function saves the events as a json in out_path.

    Parameters
    ----------
    event_name: str
        Pool event in string format (example: Mint)
    hashed_event: str
        The hashed event. Use obtain_hash_event() if necessary.
    pool_address : str
        Token address.
    out_path : str
        Path to output directory.
    start_block: float
        Starting block.
    end_block: float
        Ending block.
    """
    # this removes web3's ability to convert the address to checksum
    pool_address = shared.web3.to_checksum_address(pool_address)
    pool = shared.web3.eth.contract(pool_address, abi=shared.ABI_POOL)
    try:
        events = get_logs(pool, events_name, hashed_event, start_block, end_block, number_batches=10)
    except Exception as err:
        print(f"Exception occured: {err}")
        return

    json_events = events_to_json(events)
    print(f"Saving {pool_address}.json")
    print(f"Events: {json_events}")
    if json_events != []:
        t = ''
    with open(f'{out_path}/{pool_address}.json', 'w+') as f:
        try:
            old = json.load(f)
        except:
            old = []
        old.extend(json_events)
        json.dump(old, f)
    f.close()
