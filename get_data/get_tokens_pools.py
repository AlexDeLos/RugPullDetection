import pandas as pd
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from Utils.eth_utils import get_pools
import shared
shared.init()


def get_token_and_pools(out_path, dex='uniswap_v2', from_block = shared.BLOCKSTUDY_FROM, to_block = shared.BLOCKSTUDY):
    """
    Get tokens and pools from sushiswap or uniswap_v2.

    Parameters
    ----------
    out_path : str
        Path to output directory.
    dex : str
        sushiswap or uniswap_v2 are currently allowed.
    """

    factory = shared.web3.eth.contract(shared.UNISWAP_FACTORY, abi=shared.ABI_FACTORY)
    pool_dic, tokens = get_pools(dex, factory, from_block, to_block)
    tokens = dict((k.lower(), v) for k,v in tokens.items())
    pd.DataFrame(tokens.keys(), columns=["token_address"]).to_csv(f"{out_path}/tokens.csv", index=False)

    pool_dic = dict((k.lower(), v) for k,v in pool_dic.items())

    for pool in pool_dic.keys():
        pool_dic[pool]['token0'] = pool_dic[pool]['token0'].lower()
        pool_dic[pool]['token1'] = pool_dic[pool]['token1'].lower()
        pool_dic[pool]['address'] = pool_dic[pool]['address'].lower()
    with open(f"{out_path}/pool_dict.json", "w") as outfile:
        json.dump(pool_dic, outfile)

    inverted_pool_dict = dict()
    for pool in pool_dic.keys():
        try:
            inverted_pool_dict[pool_dic[pool]['token0']].append(pool_dic[pool])
        except:
            inverted_pool_dict[pool_dic[pool]['token0']] = [pool_dic[pool]]
        try:
            inverted_pool_dict[pool_dic[pool]['token1']].append(pool_dic[pool])
        except:
            inverted_pool_dict[pool_dic[pool]['token1']] = [pool_dic[pool]]

    with open(f"{out_path}/pools_of_token.json", "w") as outfile:
        json.dump(inverted_pool_dict, outfile)

    print('Tokens and Pools downloaded!')


# get_token_and_pools("./data_new", dex='uniswap_v2')