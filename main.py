
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
import platform
import argparse
shared.init()


parser = argparse.ArgumentParser()
parser.add_argument("--data_path", type=str, default="./temp_in_test", help="Path to data directory")
parser.add_argument("--pools", type=bool, default=False, help="Do you want to get pools and tokens again?")
# parser.add_argument("--to_block", type=int, default=shared.BLOCKSTUDY, help="Block to study")
args = parser.parse_args()

out_path = args.data_path
get_pools_and_tokens = args.pools
run_events = False
run_token_tx = False

if platform.system() == "Windows":
    # Code for Windows
    print("Running on Windows")
elif platform.system() == "Linux":
    # Code for Linux
    print("Running on Linux")
    import resource
    memory_limit = (1 * 1024 * 1024 * 1024) * 0.75  # 0,75GB

    # Set the memory limit
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
else:
    # Code for other operating systems
    print(f"Running on an unsupported operating system: {platform.system()}")


logging.basicConfig(filename="logs.log", filemode="w", format="%(name)s → %(levelname)s: %(message)s", level=logging.INFO)
# Set the memory limit in bytes

#! THIS NEEDS TO BE CHANGED TO THE CURRENT BLOCK WHEN ACTUAL TESTING STARTS
#these are block from Jet coin token

# from_block = 10008355
# eval_block =13152303 #shared.BLOCKSTUDY
from_block = 10008355
eval_block = shared.BLOCKSTUDY + 1000000
#! do the total number of transactions change anything? do I need to normalize the data?
from_block_trans = shared.BLOCKSTUDY 
eval_block_trans = shared.BLOCKSTUDY + 1000000


# This will take a while, get comfortable <3
print('starting')
if not os.path.exists(out_path):
    os.makedirs(out_path)

if get_pools_and_tokens:
    get_token_and_pools(out_path, dex='uniswap_v2', from_block = from_block, to_block = eval_block)
    # get_token_and_pools(out_path, dex='sushiswap', from_block = from_block, to_block = eval_block)
else:
    print("Not getting pools and tokens again")

# get_token_and_pools(out_path, dex='sushiswap')
logging.info("get_token_and_pools ran")
print('created tokens and pools')

# token = '0x9359CbaF496816a632A31C6D03f038f31Be6D3cf' #! no pools found for this
# token = '0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce' # -> shivainu token also gives error
# token = '0xdac17f958d2ee523a2206206994597c13d831ec7' # -> USDT, very active tokens take a LONG time
# token = '0x6B0FaCA7bA905a86F221CEb5CA404f605e5b3131' # -> DEFI token
# token = '0x8727c112C712c4a03371AC87a74dD6aB104Af768' # -> Jet coin token (healthy token)
#! token ='0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0' # -> Polygon MATIC token
token = '0x6b175474e89094c44da98b954eedeac495271d0f' # -> DAI token  _> was 1

# token = "0x1a7e4e63778b4f12a199c062f3efdd288afcbce8" # -> AGEUR token should be safe?

token = shared.web3.to_checksum_address(token)
health_tokens = pd.read_csv('./healthy_tokens.csv')
# tokens to test 21/03./2024
# token = '0x42fd79daf2a847b59d487650c68c2d7e52d752f6' # -> xTrax high risk

#! token = '0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640'

#! full scam 0x7ef1081ecc8b5b5b130656a41d4ce4f89dbbcc8c -> CP3RToken
# created on 11213887

#* Good tokens
# token = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48' # -> USDC token
# token = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2' # -> WETH token
 
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
step_size = 75000
total = len(pools_of_token.items())
current = 0
if run_events:
    for key, entry in pools_of_token.items():
        for pool in entry:
            trans_com = False
            sync_com = False
            if pool['address'] in completed_pools:
                continue
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

            if not os.path.exists(out_path + '/pool_transfer_events/'+ pool_address + '.json') and paired_with_stable:

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
                trans_com = True
                actually_transferred = True
            else:
                trans_com = True
                actually_transferred = False
            if not os.path.exists(out_path + '/pool_sync_events/'+ pool_address + '.json') and paired_with_stable:
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
                sync_com = True
                actually_synced = True
            else:
                sync_com = True
                actually_synced = False
            
            if trans_com and sync_com:
                completed_pools.append(pool_address)
            if actually_transferred and actually_synced:
                logging.info(f"Pool {pool_address} events created, {current}")
                print(f"Pool {pool_address} events created, {current}")
            else:
                logging.debug(f"Pool {pool_address} events skipped, {current}")
                print(f"Pool {pool_address} events skipped, {current}")
        current += 1
        
        print(f"Completed {current} out of {total} pools")
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

step_size = 5000
count = 0
#* run get_transfers.py

# 0x6B175474E89094C44Da98b954EedeAC495271d0F
if run_token_tx:
    for token_address in tokens:
        try:
            with open(out_path + "/Token_tx/" + token_address + ".csv", "r", encoding="utf-8", errors="ignore") as scraped:
                final_line = scraped.readlines()[-1]
                last_block = int(final_line.split(",")[1])
            new_from_block = last_block
            if new_from_block > eval_block_trans - step_size:
                completed = True
            else:
                completed = False
        except:
            new_from_block = from_block_trans
            completed = False
            

        if not completed:
            if new_from_block > from_block_trans:
                pass
            else:
                new_from_block = from_block_trans
            new_eval_block = new_from_block + step_size

            while True:
                number_of_steps = (eval_block_trans- new_from_block)//step_size
                get_transfers(token_address, out_path + "/Token_tx", new_from_block, new_eval_block)
                new_from_block = new_eval_block
                new_eval_block += step_size
                if new_eval_block > eval_block_trans:
                    new_eval_block = eval_block_trans
                    get_transfers(token_address, out_path + "/Token_tx", new_from_block, new_eval_block)
                    print(f"Token_tx {token_address} created and finished")
                    break
                
                print(f"Token_tx {token_address} created {str(count)}")
                print (f"Left {number_of_steps} steps")
                logging.info(f"Token_tx {token_address} created {str(count)}. Left {number_of_steps} steps")
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
print("Got pool features")
# for token in tokens:
# token_address (GOT IT)
# eval_block (Input)
# num_transactions (using the get_transfer_features)
transfers = pd.read_csv(out_path+f"/Token_tx/{token}.csv")
print("Got transfers")
#* Called in build_dataset.py like this: get_transfer_features(transfers.loc[transfers.block_number < eval_block].values)
# values = transfers.values #! this just kills it for some reason
print("Got values")
feature_dict = get_transfer_features(transfers)
print("Got transfer features")
# n_unique_addresses
# cluster_coeff
num_transactions, n_unique_addresses , cluster_coeff = feature_dict['num_transactions'], feature_dict['n_unique_addresses'], feature_dict['cluster_coeff']
# tx_curve
curve_dict = get_curve(transfers.values)
print("Got curve")
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
print("Got liq curve")
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
print("Got pool features")

#'num_transactions', 'n_unique_addresses', 'cluster_coeff', 'tx_curve', 'liq_curve', 'Mint', 'Burn', 'Transfer', 'difference_token_pool', 'n_syncs', 'WETH', 'prices', 'liquidity'
X_dict = {'num_transactions': num_transactions, 'n_unique_addresses': n_unique_addresses, 'cluster_coeff': cluster_coeff, 'tx_curve': tx_curve, 'liq_curve': liq_curve, 'Mint': mint, 'Burn': burn, 'Transfer': transfer, 'difference_token_pool': difference_token_pool, 'n_syncs': pool_feature_dict['n_syncs'], 'WETH': pool_feature_dict['WETH'], 'prices': pool_feature_dict['prices'], 'liquidity': pool_feature_dict['liquidity']} 
print("Got X_dict")
model = xgb.XGBClassifier()

model.load_model('models/model_0.8918918918918919.json')

X = pd.DataFrame.from_dict(X_dict)
print("Got X")

preds_scorings = model.predict_proba(X)
print("Model predicted")

preds = model.predict(X)

print("Model predicted: "+ str(preds)) #REACHED HERE
print("More precisely model predicted: "+ str(preds_scorings)) #REACHED HERE