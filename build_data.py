
import pandas as pd
from get_data.get_decimals import get_decimal_token
from get_data.get_pool_events import get_pool_events
from get_data.get_contract_creation import get_contract_creation
from get_data.get_source_code import get_source_code
from get_data.get_transfers import get_transfers
from get_data.get_tokens_pools import get_token_and_pools
import json
import subprocess
import os

import shared
shared.init()
out_path = "./data_mine_2"


# This will take a while, get comfortable <3
print('starting')
if not os.path.exists(out_path):
    os.makedirs(out_path)
# get_token_and_pools(out_path, dex='uniswap_v2')
print('created tokens and pools')

from_block = shared.BLOCKSTUDY_FROM
to_block = shared.BLOCKSTUDY


tokens_dirty = pd.read_csv(out_path + "/tokens.csv")['token_address']
health_tokens = pd.read_csv(out_path + "/healthy_tokens.csv")['token_address']
tokens = pd.concat([tokens_dirty, health_tokens], axis=0).drop_duplicates()

with open(out_path + '/pools_of_token.json', 'r') as f:
    pool_dict= json.loads(f.read())

#* Run the get_pool_events for each pool
# If the folder does not exist, it will be created
if not os.path.exists(out_path + '/pool_transfer_events'):
    os.makedirs(out_path + '/pool_transfer_events')
if not os.path.exists(out_path + '/pool_sync_events'):
    os.makedirs(out_path + '/pool_sync_events')

completed_pools = []
for key, entry in pool_dict.items():
    for pool in entry:
        trans_com = False
        sync_com = False
        if not os.path.exists(out_path + '/pool_transfer_events/'+ pool['address'] + '.json'):
            get_pool_events(['Transfer','Burn','Mint'], None , pool['address'], out_path + '/pool_transfer_events', from_block, to_block)

            trans_com = True
        else:
            trans_com = True
        if not os.path.exists(out_path + '/pool_sync_events/'+ pool['address'] + '.json'):
            get_pool_events('Sync', None , pool['address'], out_path + '/pool_sync_events', from_block, to_block)
            sync_com = True
        else:
            sync_com = True
        
        if trans_com and sync_com:
            completed_pools.append(pool['address'])
print('created pool events') #REACHED

# #* Run get_contract_creation.py 

creation_dict = {"token_address": [], "creation_block": []}
# creation_dict = pd.read_csv(out_path + "/creation.csv")
for token in tokens:
    creation_dict["token_address"].append(token)
    creation_dict["creation_block"].append(get_contract_creation(token))
df = pd.DataFrame(creation_dict)
df.to_csv(out_path + "/creation.csv", index=False)
print('created creation_dict')# REACHED HERE

#* run get_decimals.py

decimals_dict = {"token_address": [], "decimals": []}
# decimals_dict = pd.read_csv(out_path + "/decimals.csv")
decimals_dict = decimals_dict.to_dict(orient='list')
for token in tokens:
    if token not in decimals_dict["token_address"]:
        decimals_dict["token_address"].append(token)
        #184 tokens
        decimals_dict["decimals"].append(get_decimal_token(token))
    
decimals = pd.DataFrame(decimals_dict)
decimals.to_csv(out_path + "/decimals.csv", index=False)

print('created decimals_dict') #REACHED HERE

#* run get_source_code.py
if not os.path.exists(out_path + "/source_code"):
    os.makedirs(out_path + "/source_code")
for token in tokens:
    if not os.path.exists(out_path + "/source_code/" + token + ".json"):
        get_source_code(token, out_path + "/source_code")
    
print('created source_code')

if not os.path.exists(out_path + "/Token_tx"):
    os.makedirs(out_path + "/Token_tx")

#* run get_transfers.py
for token_address in tokens:
    if not os.path.exists(out_path + "/Token_tx/" + token_address + ".csv"):
        get_transfers(token_address, out_path + "/Token_tx", from_block, to_block)
print('created token_tx') #REACHED HERE


# Make token_lock_features.csv



subprocess.run(["python", "ML/Labelling/extract_pool_heuristics.py", "--data_path", out_path])

#extract_pool_heuristics.py

subprocess.run(["python", "ML/Labelling/extract_transfer_heuristics.py", "--data_path", out_path])
# extract_transfer_heuristics.py