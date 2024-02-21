#! before this can be ran you need to rin the Do_not_rug_on_me.pynb file
import pandas as pd
from get_data.get_decimals import get_decimal_token
from get_data.get_pool_events import get_pool_events
from Utils.abi_info import obtain_hash_event
import json

import shared
shared.init()

#TODO create the decimals file
# tokens = pd.read_csv("./data_mine/tokens.csv")['token_address']
# health_tokens = pd.read_csv("./data/healthy_tokens.csv")['token_address']
# # decimals_dict = {"token_address": [], "decimals": []}
# decimals_dict = pd.read_csv("./data_mine/decimals.csv")
# # for token in tokens:
# #     decimals_dict["token_address"].append(token)
# #     #184 tokens
# #     decimals_dict["decimals"].append(get_decimal_token(token))
# for token in health_tokens:
#     decimals_dict["token_address"].append(token)
#     #184 tokens
#     decimals_dict["decimals"].append(get_decimal_token(token))
# decimals = pd.DataFrame(decimals_dict)
# decimals.to_csv("./data_mine/decimals.csv", index=False)

from_block = 10008355
to_block = shared.BLOCKSTUDY


from_block = 19101714
to_block = 19101716
with open('./data/pools_of_token.json', 'r') as f:
    pool_dict= json.loads(f.read())
# pool_addresses = list(pool_dict.keys())

address1 = '0x97a6EdAD9a90346A5D49bb2FDC7348A71e2f5C6E'
address2 = '0xB6909B960DbbE7392D405429eB2b3649752b4838'

transefer_hash = obtain_hash_event('Transfer(address,address,uint256)')
has_true = '0x48dab321eda2a44b37d8d9fab92ca32ca3421cd2b7265198c26083c5b26cacf2'

pool_address = '0xB6909B960DbbE7392D405429eB2b3649752b4838'

#! INVESTIGATE THE TOPICS, how do they work
pool_dict.items()
for key, entry in pool_dict.items():
    for pool in entry:
        get_pool_events('Transaction', None , pool_address, './data/pool_sync_events', from_block, to_block)
x = 0