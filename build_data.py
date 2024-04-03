
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
import logging
# this file is to test a single token
import shared
shared.init()

logging.basicConfig(filename="logs.log", filemode="w", format="%(name)s → %(levelname)s: %(message)s", level=logging.INFO)

out_path = "./data_cluster"

#! THIS NEEDS TO BE CHANGED TO THE CURRENT BLOCK WHEN ACTUAL TESTING STARTS
#these are block from Jet coin token

# from_block = 10008355
# eval_block =13152303 #shared.BLOCKSTUDY
from_block = shared.BLOCKSTUDY 
eval_block = 19540163
#! do the total number of transactions change anything? do I need to normalize the data?
from_block_trans = shared.BLOCKSTUDY 
eval_block_trans = 19540163


# This will take a while, get comfortable <3
print('starting')
if not os.path.exists(out_path):
    os.makedirs(out_path)

get_token_and_pools(out_path, dex='uniswap_v2', from_block = from_block, to_block = eval_block)
# get_token_and_pools(out_path, dex='sushiswap', from_block = from_block, to_block = eval_block)

# get_token_and_pools(out_path, dex='sushiswap')
logging.info("get_token_and_pools ran")
print('created tokens and pools')

health_tokens = pd.read_csv('./healthy_tokens.csv')

with open(out_path + '/pools_of_token.json', 'r') as f:
    pools_of_token= json.loads(f.read())
tokens = pd.read_csv(out_path + '/tokens.csv')['token_address'].values


#* Run the get_pool_events for each pool
# If the folder does not exist, it will be created
if not os.path.exists(out_path + '/pool_transfer_events'):
    os.makedirs(out_path + '/pool_transfer_events')
if not os.path.exists(out_path + '/pool_sync_events'):
    os.makedirs(out_path + '/pool_sync_events')


# obtain_hash_event('Transfer(address,address,uint256)')
completed_pools = []
step_size = 75000
for key, entry in pools_of_token.items():
    for pool in entry:
        trans_com = False
        sync_com = False
        pool_address = shared.web3.to_checksum_address(pool['address'])
        
        if (pool['token0'] in tokens or pool['token1'] in tokens):
            # print(pool['token0'], pool['token1'])
            if any(s in tokens for s in health_tokens['token_address'].values):
                # if the token is in the health tokens then both need to be in the list
                paired_with_stable = (any(s == pool['token0'] for s in health_tokens['token_address'].values) and any(s == pool['token1'] for s in health_tokens['token_address'].values))
            else:
                paired_with_stable = (any(s == pool['token0'] for s in health_tokens['token_address'].values) or any(s == pool['token1'] for s in health_tokens['token_address'].values))
        else:
            paired_with_stable = False

        if not os.path.exists(out_path + '/pool_transfer_events/'+ pool_address + '.json'):
            if paired_with_stable:
                #obtain_hash_event('Transfer(address,address,uint256)')
                new_from_block = from_block_trans
                new_eval_block = from_block_trans + step_size
                while True:
                    get_pool_events('Transfer', obtain_hash_event('Transfer(address,address,uint256)') , pool_address, out_path + '/pool_transfer_events', new_from_block, new_eval_block)
                    new_from_block = new_eval_block
                    new_eval_block += step_size
                    if new_eval_block > eval_block_trans:
                        new_eval_block = eval_block_trans
                        get_pool_events('Transfer', obtain_hash_event('Transfer(address,address,uint256)') , pool_address, out_path + '/pool_transfer_events', new_from_block, new_eval_block)
                        break
                logging.info(f"Pool {pool_address} transfer events created")
                trans_com = True
        else:
            trans_com = True
        if not os.path.exists(out_path + '/pool_sync_events/'+ pool_address + '.json'):
            if paired_with_stable:
                new_from_block = from_block_trans
                new_eval_block = from_block_trans + step_size
                while True:
                    get_pool_events('Sync', obtain_hash_event('Sync(uint112,uint112)') , pool_address, out_path + '/pool_sync_events', new_from_block, new_eval_block)
                    new_from_block = new_eval_block
                    new_eval_block += step_size
                    if new_eval_block > eval_block_trans:
                        new_eval_block = eval_block_trans
                        get_pool_events('Sync', obtain_hash_event('Sync(uint112,uint112)') , pool_address, out_path + '/pool_sync_events', new_from_block, new_eval_block)
                        break
                    logging.info(f"Pool {pool_address} sync events created")
                sync_com = True
        else:
            sync_com = True
        
        if trans_com and sync_com:
            completed_pools.append(pool_address)
logging.info("Completed pools ------------------------------------------------")
print('created pool events') #REACHED

# #* Run get_contract_creation.py 
# ! this is not needed

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

logging.info("Decimals created ------------------------------------------------")
print('created decimals_dict') #REACHED HERE

#* run get_source_code.py
if not os.path.exists(out_path + "/source_code"):
    os.makedirs(out_path + "/source_code")
for token in tokens:
    if not os.path.exists(out_path + "/source_code/" + token + ".json"):
        get_source_code(token, out_path + "/source_code")
logging.info("Source code created ------------------------------------------------")
print('created source_code')

if not os.path.exists(out_path + "/Token_tx"):
    os.makedirs(out_path + "/Token_tx")

step_size = 500
count = 0
#* run get_transfers.py
for token_address in tokens:
    try:
        with open(out_path + "/Token_tx/" + token_address + ".csv", "r", encoding="utf-8", errors="ignore") as scraped:
            final_line = scraped.readlines()[-1]
            last_block = int(final_line.split(",")[1])
        new_from_block = last_block
        if new_from_block > eval_block_trans:
            completed = True
        else:
            completed = False
    except:
        completed = False
        

    if not completed:
        if new_from_block > from_block_trans - step_size:
            pass
        else:
            new_from_block = from_block_trans
        new_eval_block = from_block_trans + step_size
        while True:
            get_transfers(token_address, out_path + "/Token_tx", new_from_block, new_eval_block)
            new_from_block = new_eval_block
            new_eval_block += step_size
            if new_eval_block > eval_block_trans:
                new_eval_block = eval_block_trans
                get_transfers(token_address, out_path + "/Token_tx", new_from_block, new_eval_block)
                print(f"Token_tx {token_address} created and finished")
                break
            print(f"Token_tx {token_address} created {str(count)}")
            logging.info(f"Token_tx {token_address} created {str(count)}")
            count += 1

logging.info("Token_tx created ------------------------------------------------")
print('created token_tx') #REACHED HERE

#* RAN IT UP TO HERE

# Make token_lock_features.csv


#extract_pool_heuristics.py

# python ML/Labelling/extract_pool_heuristics.py --data_path ./temp_in_test --token 0x6b175474e89094c44da98b954eedeac495271d0f --to_block 13152303
print("Running extract_pool_heuristics, on token: ", token)
logging.info(f"Running extract_pool_heuristics, on token: {token}")
subprocess.run(["python", "ML/Labelling/extract_pool_heuristics.py", "--data_path", out_path, "--token", str(tokens[0]), "--to_block", str(eval_block_trans)])
# extract_transfer_heuristics.py
logging.info("extract_pool_heuristics ran")
print("Running extract_transfer_heuristics, on token: ", token)
logging.info(f"Running extract_transfer_heuristics, on token: {token}")
# python ML/Labelling/extract_transfer_heuristics.py --data_path ./temp_in_test --token 0x6b175474e89094c44da98b954eedeac495271d0f --to_block 13152303
subprocess.run(["python", "ML/Labelling/extract_transfer_heuristics.py", "--data_path", out_path, "--token", str(tokens[0]), "--to_block", str(eval_block_trans)])
logging.info("extract_transfer_heuristics ran")

# subprocess.run(["python", "ML/build_dataset.py", "--data_path", out_path, "--token", token]) #! this is not needed

pool_features = pd.read_csv(out_path+"/pool_heuristics.csv", index_col="token_address")
# for token in tokens:
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
features = pool_features.loc[token]
pool_address = features['pool_address']
print("pool_address: ")
print(pool_address)
# pool_addresses = []
# lp_transfers_json = []
# for pool in pools_of_token[token]:
#     pool_addresses.append(pool['address'])

with open(out_path+f'/pool_transfer_events/{pool_features.loc[token]["pool_address"]}.json',
            'r') as f:
    lp_transfers_json = json.loads(f.read())
    lp_transfers = pd.DataFrame([[info['transactionHash'], info['blockNumber']] + list(info['args'].values())
                                    + [info['event']] # [info['type']] for info in lp_transfers])
                                    for info in lp_transfers_json])

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
features = pool_features.loc[token]
pool_address = features['pool_address']
WETH_pools = pools_of_token[shared.WETH]

WETH_pool_address = {pool_info['address']: pool_info for pool_info in WETH_pools}  # Set pool address as key
pool_info = WETH_pool_address[pool_address]
WETH_position = 1 if shared.WETH == pool_info['token1'] else 0
with open(out_path+f'/pool_sync_events/{pool_address}.json', 'r') as f:
    syncs = json.loads(f.read())
    
syncs = pd.DataFrame([[info['blockNumber']] + list(info['args'].values()) for info in syncs])
syncs.columns = ['blockNumber', 'reserve0', 'reserve1']
decimals = pd.read_csv(out_path+"/decimals.csv", index_col="token_address")
decimal = decimals.loc[token].iloc[0]
pool_feature_dict = get_pool_features(syncs.loc[syncs.blockNumber < eval_block_trans], WETH_position, decimal)

#'num_transactions', 'n_unique_addresses', 'cluster_coeff', 'tx_curve', 'liq_curve', 'Mint', 'Burn', 'Transfer', 'difference_token_pool', 'n_syncs', 'WETH', 'prices', 'liquidity'
X_dict = {'num_transactions': num_transactions, 'n_unique_addresses': n_unique_addresses, 'cluster_coeff': cluster_coeff, 'tx_curve': tx_curve, 'liq_curve': liq_curve, 'Mint': mint, 'Burn': burn, 'Transfer': transfer, 'difference_token_pool': difference_token_pool, 'n_syncs': pool_feature_dict['n_syncs'], 'WETH': pool_feature_dict['WETH'], 'prices': pool_feature_dict['prices'], 'liquidity': pool_feature_dict['liquidity']} 
model = xgb.XGBClassifier()

model.load_model('models/model_0.8918918918918919.json')

X = pd.DataFrame.from_dict(X_dict)

preds_scorings = model.predict_proba(X)

preds = model.predict(X)

print("Model predicted: "+ str(preds)) #REACHED HERE
print("More precisely model predicted: "+ str(preds_scorings)) #REACHED HERE