
import pandas as pd
from get_data.get_decimals import get_decimal_token
from get_data.get_pool_events import get_pool_events
from get_data.get_source_code import get_source_code
from get_data.get_transfers import get_transfers
from get_data.get_contract_creation import get_contract_creation
from get_data.get_tokens_pools import get_token_and_pools
from features.transfer_features import get_transfer_features, get_curve
from Utils.abi_info import obtain_hash_event
from features.pool_features import get_pool_features
import xgboost as xgb
import subprocess
import json
import os
# this file is to test a single token
import shared
shared.init()

out_path = "./temp_in"

#! THIS NEEDS TO BE CHANGED TO THE CURRENT BLOCK WHEN ACTUAL TESTING STARTS
#these are block from Shivainu token
from_block = 10522038
eval_block = 15411914


# This will take a while, get comfortable <3
print('starting')
if not os.path.exists(out_path):
    os.makedirs(out_path)
# get_token_and_pools(out_path, dex='uniswap_v2', from_block = from_block, to_block = eval_block)
# get_token_and_pools(out_path, dex='sushiswap')
print('created tokens and pools')

# token = '0x9359CbaF496816a632A31C6D03f038f31Be6D3cf' #! no pools found for this
token = '0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce'.lower() # -> shivainu token also gives error
# token = '0xdac17f958d2ee523a2206206994597c13d831ec7' # -> USDT, very active tokens take a LONG time


with open(out_path + '/pools_of_token.json', 'r') as f:
    pools_of_token= json.loads(f.read())
tokens = [token]


#* Run the get_pool_events for each pool
# If the folder does not exist, it will be created
if not os.path.exists(out_path + '/pool_transfer_events'):
    os.makedirs(out_path + '/pool_transfer_events')
if not os.path.exists(out_path + '/pool_sync_events'):
    os.makedirs(out_path + '/pool_sync_events')


# obtain_hash_event('Transfer(address,address,uint256)')
completed_pools = []
for key, entry in pools_of_token.items():
    for pool in entry:
        trans_com = False
        sync_com = False
        if not os.path.exists(out_path + '/pool_transfer_events/'+ pool['address'] + '.json'):
            if pool['token0'] == token or pool['token1'] == token:
                get_pool_events('Transfer', obtain_hash_event('Transfer(address,address,uint256)') , pool['address'], out_path + '/pool_transfer_events', from_block, eval_block)
                get_pool_events('Burn', obtain_hash_event('Burn(address,uint256)') , pool['address'], out_path + '/pool_transfer_events', from_block, eval_block)
                get_pool_events('Mint', obtain_hash_event('Mint(address,uint256)') , pool['address'], out_path + '/pool_transfer_events', from_block, eval_block)
                # get_pool_events(['Transfer','Burn','Mint'], None , pool['address'], out_path + '/pool_transfer_events', from_block, eval_block)
                trans_com = True
        else:
            trans_com = True
        if not os.path.exists(out_path + '/pool_sync_events/'+ pool['address'] + '.json'):
            if pool['token0'] == token or pool['token1'] == token:
                # get_pool_events('Sync', None , pool['address'], out_path + '/pool_sync_events', from_block, eval_block)
                get_pool_events('Sync', obtain_hash_event('Sync(uint112,uint112)') , pool['address'], out_path + '/pool_sync_events', from_block, eval_block)
                sync_com = True
        else:
            sync_com = True
        
        if trans_com and sync_com:
            completed_pools.append(pool['address'])
print('created pool events') #REACHED

# #* Run get_contract_creation.py 

# creation_dict = {"token_address": [], "creation_block": []}

# for token in tokens:
#     creation_dict["token_address"].append(token)
#     creation_dict["creation_block"].append(get_contract_creation(token))
# df = pd.DataFrame(creation_dict)
# df.to_csv(out_path + "/creation.csv", index=False)
# print('created creation_dict')# REACHED HERE

#* run get_decimals.py

decimals_dict = {"token_address": [], "decimals": []}
for token in tokens:
    if token not in decimals_dict["token_address"]:
        decimals_dict["token_address"].append(token)
        #184 tokens
        try:
            decimals_dict["decimals"].append(get_decimal_token(token))
        except:
            decimals_dict["decimals"].append(18)
    
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
        get_transfers(token_address, out_path + "/Token_tx", from_block, eval_block)
print('created token_tx') #REACHED HERE

#* RAN IT UP TO HERE

# Make token_lock_features.csv


#extract_pool_heuristics.py

subprocess.run(["python", "ML/Labelling/extract_pool_heuristics.py", "--data_path", out_path, "--token", token])
# extract_transfer_heuristics.py

subprocess.run(["python", "ML/Labelling/extract_transfer_heuristics.py", "--data_path", out_path, "--token", token, "--to_block", str(eval_block)])


# subprocess.run(["python", "ML/build_dataset.py", "--data_path", out_path, "--token", token]) #! this is not needed


# token_address (GOT IT)
# eval_block (Input)
# num_transactions (using the get_transfer_features)
transfers = pd.read_csv(out_path+f"/Token_tx/{token}.csv")
#* Called in build_dataset.py like this: get_transfer_features(transfers.loc[transfers.block_number < eval_block].values)
feature_dict = get_transfer_features(transfers.values)
# n_unique_addresses
# cluster_coeff
num_transactions, n_unique_addresses , cluster_coeff = feature_dict['num_transactions'], feature_dict['n_unique_addresses'], feature_dict['cluster_coeff']
# tx_curve
curve_dict = get_curve(transfers.values)
tx_curve = curve_dict['tx_curve']

# liq_curve
pool_addresses = pools_of_token[token][0]['address']

with open(out_path+f'/pool_transfer_events/{pool_addresses}.json',
            'r') as f:
    lp_transfers_json = json.loads(f.read())

lp_transfers = pd.DataFrame([[info['transactionHash'], info['blockNumber']] + list(info['args'].values())
                    + [info['event']]
                    for info in lp_transfers_json])
del lp_transfers[6]
lp_transfers.columns = list(transfers.columns) + ['type']
# called like this on build_dataset: get_curve(lp_transfers.loc[lp_transfers.block_number < eval_block].values)['tx_curve']})
liq_curve = get_curve(lp_transfers.values)
# Mint
# Burn
# Transfer
# transfer_types = lp_transfers.loc[lp_transfers.block_number < eval_block]['type'].value_counts()
transfer_types = lp_transfers['type'].value_counts()
dic_of_trans = {'Mint': 0, 'Burn': 0, 'Transfer': 0}
for type_ in transfer_types.index:
    dic_of_trans[type_] = transfer_types[type_]
mint, burn, transfer = dic_of_trans['Mint'], dic_of_trans['Burn'], dic_of_trans['Transfer']
# difference_token_pool
difference_token_pool = lp_transfers['block_number'].iloc[0] - transfers['block_number'].iloc[0]
# n_syncs
# WETH
# prices
# liquidity
pool_features = pd.read_csv(out_path+"/pool_heuristics.csv", index_col="token_address")
features = pool_features.loc[token]
pool_address = features['pool_address']
WETH_pools = pools_of_token[shared.WETH.lower()]

WETH_pool_address = {pool_info['address']: pool_info for pool_info in WETH_pools}  # Set pool address as key
pool_info = WETH_pool_address[pool_address]
WETH_position = 1 if shared.WETH.lower() == pool_info['token1'] else 0
with open(out_path+f'/pool_sync_events/{pool_address}.json', 'r') as f:
    syncs = json.loads(f.read())
    
syncs = pd.DataFrame([[info['blockNumber']] + list(info['args'].values()) for info in syncs])
syncs.columns = ['blockNumber', 'reserve0', 'reserve1']
decimals = pd.read_csv(out_path+"/decimals.csv", index_col="token_address")
decimal = decimals.loc[token].iloc[0]
pool_feature_dict = get_pool_features(syncs.loc[syncs.blockNumber < eval_block], WETH_position, decimal)

#'num_transactions', 'n_unique_addresses', 'cluster_coeff', 'tx_curve', 'liq_curve', 'Mint', 'Burn', 'Transfer', 'difference_token_pool', 'n_syncs', 'WETH', 'prices', 'liquidity'
X_dict = {'num_transactions': num_transactions, 'n_unique_addresses': n_unique_addresses, 'cluster_coeff': cluster_coeff, 'tx_curve': tx_curve, 'liq_curve': liq_curve, 'Mint': mint, 'Burn': burn, 'Transfer': transfer, 'difference_token_pool': difference_token_pool, 'n_syncs': pool_feature_dict['n_syncs'], 'WETH': pool_feature_dict['WETH'], 'prices': pool_feature_dict['prices'], 'liquidity': pool_feature_dict['liquidity']} 
model = xgb.XGBClassifier()

model.load_model('models/model_0.8918918918918919.json')

X = pd.DataFrame.from_dict(X_dict)

preds_scorings = model.predict_proba(X)

preds = model.predict(X)

print("Model predicted: "+ str(preds)) #REACHED HERE
print("More precisely model predicted: "+ str(preds_scorings)) #REACHED HERE