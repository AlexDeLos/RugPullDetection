
import pandas as pd
from get_data.get_decimals import get_decimal_token
from get_data.get_pool_events import get_pool_events
from get_data.get_contract_creation import get_contract_creation
from get_data.get_source_code import get_source_code
from get_data.get_transfers import get_transfers
from get_data.get_tokens_pools import get_token_and_pools
import json
import os

import shared
shared.init()
out_path = "./data_mine"


# This will take a while, get comfortable <3
print('starting')
if not os.path.exists(out_path):
    os.makedirs(out_path)
get_token_and_pools(out_path, dex='uniswap_v2')
print('created tokens and pools')

#TODO create the decimals file


# from_block = 10008355
from_block = shared.BLOCKSTUDY - 7500 # approx one day
to_block = shared.BLOCKSTUDY

tokens = pd.read_csv(out_path + "/tokens.csv")['token_address']
health_tokens = pd.read_csv(out_path + "/healthy_tokens.csv")['token_address']
tokens = pd.concat([tokens, health_tokens], axis=0).drop_duplicates()

with open(out_path + '/pools_of_token.json', 'r') as f:
    pool_dict= json.loads(f.read())
    
#* Run the get_pool_events for each pool
# If the folder does not exist, it will be created
if not os.path.exists(out_path + '/pool_transfer_events'):
    os.makedirs(out_path + '/pool_transfer_events')
# if not os.path.exists(out_path + '/pool_swap_events'):
#     os.makedirs(out_path + '/pool_swap_events')
# if not os.path.exists(out_path + '/pool_approve_events'):
#     os.makedirs(out_path + '/pool_approve_events')
if not os.path.exists(out_path + '/pool_sync_events'):
    os.makedirs(out_path + '/pool_sync_events')
pool_dict.items()
for key, entry in pool_dict.items():
    for pool in entry:
        # get_pool_events('Transfer', None , pool['address'], out_path + '/pool_transfer_events', from_block, to_block)
        # get_pool_events('Swap', None , pool['address'], out_path + '/pool_swap_events', from_block, to_block)
        # get_pool_events('Approve', None , pool['address'], out_path + '/pool_approve_events', from_block, to_block)
        get_pool_events('Sync', None , pool['address'], out_path + '/pool_sync_events', from_block, to_block)
print('created pool events') #REACHED

#* Run get_contract_creation.py 

creation_dict = {"token_address": [], "creation_block": []}
# creation_dict = pd.read_csv(out_path + "/creation.csv")
for token in tokens:
    creation_dict["token_address"].append(token)
    #184 tokens
    creation_dict["creation_block"].append(get_contract_creation(token))

print('created creation_dict')# REACHED HERE

#* run get_decimals.py

decimals_dict = {"token_address": [], "decimals": []}
# decimals_dict = pd.read_csv(out_path + "/decimals.csv")
for token in tokens:
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
    get_source_code(token, out_path + "/source_code")
    
print('created source_code')

if not os.path.exists(out_path + "/transfers"):
    os.makedirs(out_path + "/transfers")

#* run get_transfers.py
for token_address in tokens:
    get_transfers(token_address, out_path + "/transfers", from_block, to_block)