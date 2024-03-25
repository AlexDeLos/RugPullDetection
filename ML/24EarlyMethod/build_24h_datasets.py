import pandas as pd
import json
import os
import sys

#add path to root folder of repository
sys.path.append(os.getcwd())
import shared

shared.init()

from features.pool_features import get_pool_features
from features.transfer_features import get_transfer_features, get_curve

data_path = shared.DATA_PATH

df = pd.read_csv(data_path + "/labeled_list.csv", index_col="token_address")
pool_features = pd.read_csv(data_path + "/pool_heuristics.csv", index_col="token_address")
decimals = pd.read_csv(data_path + "/decimals.csv", index_col="token_address")
with open(data_path + '/pools_of_token.json', 'r') as f:
    pool_of_token = json.loads(f.read())

WETH_pools = pool_of_token[shared.WETH]
WETH_pool_address = {pool_info['address']: pool_info for pool_info in WETH_pools}   # Set pool address as key


for hour in range(13, 25):
    iteration = 0
    final_dataset = []
    for address, label, type_ in zip(df.index.tolist(), df['label'], df['type']):
        features = pool_features.loc[address]
        pool_address = features['pool_address']
        pool_info = WETH_pool_address[pool_address]

        first_block = int(features['first_sync_block'])
        eval_block = first_block + 300 * hour

        #  Open token transfers, lp transfers and syncs.
        try:
            # Open token transfers
            transfers = pd.read_csv(data_path + f"/Token_tx/{address}.csv")
            if transfers.empty:
                print(f"Empty transfer file for {address}")
                continue

            # Open lp transfers
            with open(data_path + f'/pool_transfer_events/'
                      f'{pool_features.loc[address]["pool_address"]}.json', 'r') as f:
                lp_transfers = json.loads(f.read())
                lp_transfers = pd.DataFrame([[info['transactionHash'], info['blockNumber']]
                                             + list(info['args'].values()) + [info['event']]
                                             for info in lp_transfers])
            lp_transfers.columns = list(transfers.columns) + ['type']

            # Pool features
            with open(data_path + f'/pool_sync_events/{pool_address}.json', 'r') as f:
                syncs = json.loads(f.read())  # Open sync events
            syncs = pd.DataFrame([[info['blockNumber']] + list(info['args'].values()) for info in syncs])
            syncs.columns = ['blockNumber', 'reserve0', 'reserve1']

        except Exception as err:
            print(err)
            continue

        WETH_position = 1 if shared.WETH == pool_info['token1'] else 0
        decimal = decimals.loc[address].iloc[0]

        computed_features = {}

        # Transfer Features
        computed_features.update({'token_address': address, 'eval_block': eval_block})
        computed_features.update(get_transfer_features(transfers.loc[transfers.block_number < eval_block].values))
        computed_features.update(get_curve(transfers.loc[transfers.block_number < eval_block].values))

        # Lp Transfer Features
        computed_features.update({'liq_curve': get_curve(
            lp_transfers.loc[lp_transfers.block_number < eval_block].values)['tx_curve']})

        transfer_types = lp_transfers.loc[lp_transfers.block_number < eval_block]['type'].value_counts()
        computed_features.update({'Mint': 0, 'Burn': 0, 'Transfer': 0})
        for _type_ in transfer_types.index:
            computed_features[_type_] = transfer_types[_type_]
        computed_features.update({'difference_token_pool': + lp_transfers['block_number'].iloc[0]
                                                           - transfers['block_number'].iloc[0]})

        #  Sync Features
        computed_features.update(get_pool_features(syncs[syncs.blockNumber < eval_block], WETH_position, decimal))

        final_dataset.append(computed_features)

        iteration += 1
        print(hour, iteration, len(df.index.tolist()))

    pd.DataFrame(final_dataset).to_csv(data_path + f"/hours_dataset/X_{hour}h.csv", index=False)
