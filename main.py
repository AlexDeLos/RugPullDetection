
import pandas as pd
from get_data.get_decimals import get_decimal_token
from get_data.get_pool_events import get_pool_events
from get_data.get_source_code import get_source_code
from get_data.get_transfers import get_transfers
from features.transfer_features import get_transfer_features, get_curve
from features.pool_features import get_pool_features
import xgboost as xgb
import subprocess
import json
import os
# this file is to test a single token
import shared
shared.init()
out_path = "./temp_in"

# This will take a while, get comfortable <3
print('starting')
if not os.path.exists(out_path):
    os.makedirs(out_path)
# get_token_and_pools(out_path, dex='uniswap_v2')
print('created tokens and pools')

token = '0x774fb37e50DB4BF53b7C08e6B71007bf1F1D9a47'
with open(out_path + '/pools_of_token.json', 'r') as f:
    pools_of_token= json.loads(f.read())
from_block = shared.BLOCKSTUDY_FROM
to_block = shared.BLOCKSTUDY
tokens = [token]


#* Run the get_pool_events for each pool
# If the folder does not exist, it will be created
if not os.path.exists(out_path + '/pool_transfer_events'):
    os.makedirs(out_path + '/pool_transfer_events')
if not os.path.exists(out_path + '/pool_sync_events'):
    os.makedirs(out_path + '/pool_sync_events')

completed_pools = []
for key, entry in pools_of_token.items():
    for pool in entry:
        trans_com = False
        sync_com = False
        if not os.path.exists(out_path + '/pool_transfer_events/'+ pool['address'] + '.json'):
            if pool['token0'] == token or pool['token1'] == token:
                get_pool_events(['Transfer','Burn','Mint'], None , pool['address'], out_path + '/pool_transfer_events', from_block, to_block)
                trans_com = True
        else:
            trans_com = True
        if not os.path.exists(out_path + '/pool_sync_events/'+ pool['address'] + '.json'):
            if pool['token0'] == token or pool['token1'] == token:
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
# for token in tokens:
#     creation_dict["token_address"].append(token)
#     #184 tokens
#     creation_dict["creation_block"].append(get_contract_creation(token))
# df = pd.DataFrame(creation_dict)
# df.to_csv(out_path + "/creation.csv", index=False)
print('created creation_dict')# REACHED HERE

#* run get_decimals.py

decimals_dict = {"token_address": [], "decimals": []}
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

#* RAN IT UP TO HERE

# Make token_lock_features.csv


#extract_pool_heuristics.py

# subprocess.run(["python", "ML/Labelling/extract_pool_heuristics.py", "--data_path", out_path, "--token", token])
# extract_transfer_heuristics.py

# subprocess.run(["python", "ML/Labelling/extract_transfer_heuristics.py", "--data_path", out_path, "--token", token])


subprocess.run(["python", "ML/build_dataset.py", "--data_path", out_path, "--token", token])
# token_address (GOT IT)
# eval_block (Input)
# num_transactions (using the get_transfer_features)
transfers = pd.read_csv(out_path+f"/Token_tx/{token}.csv")
#* Called in build_dataset.py like this: get_transfer_features(transfers.loc[transfers.block_number < eval_block].values)
feature_dict = get_transfer_features(transfers)
# n_unique_addresses
# cluster_coeff
num_transactions, n_unique_addresses , cluster_coeff = feature_dict['num_transactions'], feature_dict['n_unique_addresses'], feature_dict['cluster_coeff']
# tx_curve
curve_dict = get_curve(transfers)
tx_curve = curve_dict['tx_curve']
# liq_curve
pool_addresses = pools_of_token[token][0]['address']

with open(out_path+f'/pool_transfer_events/{pool_addresses}.json',
            'r') as f:
    lp_transfers = json.loads(f.read())
    lp_transfers = pd.DataFrame([[info['transactionHash'], info['blockNumber']] + list(info['args'].values())
                                    + [info['event']]
                                    for info in lp_transfers])

lp_transfers.columns = list(transfers.columns) + ['type']
# called like this on build_dataset: get_curve(lp_transfers.loc[lp_transfers.block_number < eval_block].values)['tx_curve']})
liq_curve = get_curve(lp_transfers)
# Mint
# Burn
# Transfer
# transfer_types = lp_transfers.loc[lp_transfers.block_number < eval_block]['type'].value_counts()
transfer_types = lp_transfers['type'].value_counts()
dic_of_trans = {'Mint': 0, 'Burn': 0, 'Transfer': 0}
for type_ in transfer_types.index:
    dic_of_trans[type_] = transfer_types[type_]
# difference_token_pool
difference_token_pool = lp_transfers['block_number'].iloc[0] - transfers['block_number'].iloc[0]
# n_syncs
# WETH
# prices
# liquidity
pool_features = pd.read_csv(out_path+"/pool_heuristics.csv", index_col="token_address")
features = pool_features.loc[token]
pool_address = features['pool_address']
WETH_pools = pools_of_token[shared.WETH]

WETH_pool_address = {pool_info['address']: pool_info for pool_info in WETH_pools}  # Set pool address as key
pool_info = WETH_pool_address[pool_address]
WETH_position = 1 if shared.WETH == pool_info['token1'] else 0
with open(out_path+f'/pool_sync_events/{pool_address}.json', 'r') as f:
    syncs = json.loads(f.read())
decimals = pd.read_csv(out_path+"/decimals.csv", index_col="token_address")
decimal = decimals.loc[token].iloc[0]
pool_feature_dict = get_pool_features(syncs.loc[syncs.blockNumber < eval_block], WETH_position, decimal)

X = pd.read_csv("X.csv")
X = X.set_index("token_address")
#! WE DO NOT NEED THE LABELS
# labels = pd.read_csv("./ML/Labelling/labeled_list.csv", index_col="token_address")
X = X.merge(labels['label'], left_index=True, right_index=True)
X = X.reset_index()
df = X.drop_duplicates(subset=['token_address'])
X = X.set_index("token_address")
lock_features = pd.read_csv("./data_mine/token_lock_features.csv", index_col="token_address") #! Where do they get this from?

model = xgb.XGBClassifier()

model.load_model('models/model_0.8918918918918919.json')
model.predict()