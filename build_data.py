
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
parser.add_argument("--data_path", type=str, default="./full_data", help="Path to data directory")
parser.add_argument("--pools", type=bool, default=False, help="Do you want to get pools and tokens again?")
parser.add_argument("--token" , type=str, default=None, help="Token to study")
parser.add_argument("-e", "--events", type=bool, default=False, help="run event gathering")
parser.add_argument("-t", "--token_tx", type=bool, default=False, help="run token tx gathering")
# parser.add_argument("--to_block", type=int, default=shared.BLOCKSTUDY, help="Block to study")
args = parser.parse_args()

out_path = args.data_path
get_pools_and_tokens = args.pools
run_events = args.events
run_token_tx = args.token_tx
token = args.token
print(run_events)
print(run_token_tx)
print(f"arguments: {args}")

if platform.system() == "Windows":
    # Code for Windows
    print("Running on Windows")
elif platform.system() == "Linux":
    # Code for Linux
    print("Running on Linux")
    # import resource
    # memory_limit = (1 * 1024 * 1024 * 1024) * 2  # 0,75GB

    # # Set the memory limit
    # resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
else:
    # Code for other operating systems
    print(f"Running on an unsupported operating system: {platform.system()}")


logging.basicConfig(filename="log_build_data.log", filemode="w", format="%(name)s → %(levelname)s: %(message)s", level=logging.DEBUG)
# Set the memory limit in bytes

#! THIS NEEDS TO BE CHANGED TO THE CURRENT BLOCK WHEN ACTUAL TESTING STARTS
#these are block from Jet coin token

#! do the total number of transactions change anything? do I need to normalize the data?
from_block_trans = shared.BLOCKSTUDY_FROM 
eval_block_trans = shared.BLOCKSTUDY


# This will take a while, get comfortable <3
print('starting')

try:
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    if get_pools_and_tokens:
        get_token_and_pools(out_path, dex='uniswap_v2', from_block = from_block_trans, to_block = eval_block_trans)
        # get_token_and_pools(out_path, dex='sushiswap', from_block_trans = from_block_trans, to_block = eval_block_trans)
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
    # token = '0x6b175474e89094c44da98b954eedeac495271d0f' # -> DAI token  _> was 1 -> confirmed to be safe

    # token = "0x1a7e4e63778b4f12a199c062f3efdd288afcbce8" # -> AGEUR token should be safe?
    health_tokens = pd.read_csv('./healthy_tokens.csv')

    tokens = pd.read_csv(out_path + '/tokens.csv')['token_address'].values

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


    #* Run the get_pool_events for each pool
    # If the folder does not exist, it will be created
    if not os.path.exists(out_path + '/pool_transfer_events'):
        os.makedirs(out_path + '/pool_transfer_events')
    if not os.path.exists(out_path + '/pool_sync_events'):
        os.makedirs(out_path + '/pool_sync_events')


    # obtain_hash_event('Transfer(address,address,uint256)')
    completed_pools = []
    step_size = 3000
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

                paired_with_stable = (any(s == pool['token0'] for s in health_tokens['token_address'].values) or any(s == pool['token1'] for s in health_tokens['token_address'].values))

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
    if os.path.exists(out_path + "/decimals.csv"):
        print("Decimals already exist")
        decimals_dict = pd.read_csv(out_path + "/decimals.csv")
        # turn this 2 columns (token_address,decimals) csv to a dictionary with token_address and decimals as keys
        # has to fit this structure {"token_address": [], "decimals": []}
        decimals_dict = decimals_dict.to_dict('list')
    else:
        decimals_dict = {"token_address": [], "decimals": []}
    total_tokens = len(tokens)
    count = 0
    for token in tokens:
        print(f"Getting decimals for {count} out of {total_tokens}")
        if token not in decimals_dict["token_address"]:
            decimals_dict["token_address"].append(token)
            #184 tokens
            decimal = get_decimal_token(token)
            try:
                decimals_dict["decimals"].append(decimal)
                # print(f"Token {token} has {decimal} decimals")
            except:
                # if decimal == -999:
                #     raise Exception("Too many requests")
                decimals_dict["decimals"].append(18)
                # print(f"Token {token} has been given 18 decimals")
        count += 1
        if count % 1000 == 0:
            print(f"Decimals for {count} out of {total_tokens} have been saved")
            decimals = pd.DataFrame(decimals_dict)
            decimals.to_csv(out_path + "/decimals.csv", index=False)
    decimals = pd.DataFrame(decimals_dict)
    # print(decimals)
    decimals.to_csv(out_path + "/decimals.csv", index=False)

    logging.info("Decimals created ------------------------------------------------")
    print('created decimals_dict') #REACHED HERE

    #* run get_source_code.py
    # if not os.path.exists(out_path + "/source_code"):
    #     os.makedirs(out_path + "/source_code")
    # for token in tokens:
    #     if not os.path.exists(out_path + "/source_code/" + token + ".json"):
    #         get_source_code(token, out_path + "/source_code")
    # logging.info("Source code created ------------------------------------------------")
    # print('created source_code')

    if not os.path.exists(out_path + "/Token_tx"):
        os.makedirs(out_path + "/Token_tx")

    step_size = 2000
    count = 0
    #* run get_transfers.py

    # 0x6B175474E89094C44Da98b954EedeAC495271d0F
    
    tokens_skip = ['0x7674d5Fa0f17a9A027f49f6c3B32046770E076eA','0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2']# done or long tokens
    if run_token_tx:
        count_tokens = 0
        len_tokens = len(tokens)
        for token_address in tokens:
            # if token_address in tokens_skip:
            #     continue
            try:
                # print(f"Getting last block for {token_address}")
                transfers = pd.read_csv(out_path + "/Token_tx/" + token_address + ".csv", iterator=True, chunksize=1000, index_col=0)
                last_block = 0
                for transfer in transfers:
                    cur_max = transfer['block_number'].max()
                    if cur_max > last_block:
                        last_block = cur_max
                # print(f"Last block for {token_address} is {last_block}")
                new_from_block = last_block
                if new_from_block > eval_block_trans - step_size:
                    completed = True
                    print(f"Token_tx {token_address} created and finished")
                else:
                    completed = False
            except Exception as e:
                new_from_block = from_block_trans
                completed = False
                print("Problem getting last block")
                print(e)
                

            if not completed:
                if new_from_block > from_block_trans:
                    pass
                else:
                    new_from_block = from_block_trans
                new_eval_block = new_from_block + step_size

                while True:
                    number_of_steps = (eval_block_trans- new_from_block)//step_size
                    if new_from_block!=new_eval_block:
                        get_transfers(token_address, out_path + "/Token_tx", new_from_block, new_eval_block)
                    new_from_block = new_eval_block
                    new_eval_block += step_size
                    if new_eval_block > eval_block_trans:
                        new_eval_block = eval_block_trans
                        get_transfers(token_address, out_path + "/Token_tx", new_from_block, new_eval_block)
                        print(f"Token_tx {token_address} created and finished")
                        break
                    
                    # print(f"Token_tx {token_address} created {str(count)}")
                    # print (f"Left {number_of_steps} steps")
                    logging.info(f"Token_tx {token_address} created {str(count)}. Left {number_of_steps} steps")
                    count += 1
            logging.info(f"Token_tx {token_address} created ------------------------------------------------")
            print(f"Token_tx {token_address} created ------------------------------------------------")
            count_tokens += 1
            logging.info(f"Token_tx {token_address} created {str(count_tokens)} out of {len_tokens}")
            print(f"Token_tx {token_address} created {str(count_tokens)} out of {len_tokens}")

    logging.info("Token_tx created ------------------------------------------------")
    print('created token_tx') #REACHED HERE

    #* RAN IT UP TO HERE

    # Make token_lock_features.csv


    #extract_pool_heuristics.py

    # python ML/Labelling/extract_pool_heuristics.py --data_path ./temp_in_test --token 0x6b175474e89094c44da98b954eedeac495271d0f --to_block 13152303
    print("Running extract_pool_heuristics, on token: ", token)
    # logging.info(f"Running extract_pool_heuristics, on token: {token}")
    subprocess.run(["python", "ML/Labelling/extract_pool_heuristics.py", "--data_path", out_path, "--to_block", str(eval_block_trans)])
    # extract_transfer_heuristics.py
    print("extract_pool_heuristics ran")
    # print("Running extract_transfer_heuristics, on token: ", token)
    # logging.info(f"Running extract_transfer_heuristics, on token: {token}")
    subprocess.run(["python", "ML/Labelling/extract_transfer_heuristics.py", "--data_path", out_path, "--to_block", str(eval_block_trans)])
    print("extract_transfer_heuristics ran")
    # need to run assing label.py
    # subprocess.run(["python", "ML/build_dataset.py", "--data_path", out_path, "--token", token]) #! this is not needed
    # logging.info("build_dataset ran")
except Exception as e:
    logging.error(f"Error: {e}")
    print(f"Error: {e}")
    raise e