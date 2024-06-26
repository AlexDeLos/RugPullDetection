import sys
import pandas as pd
import os
import ast
import argparse
sys.path.append(os.getcwd())
import shared
shared.init()


parser = argparse.ArgumentParser()
parser.add_argument("--data_path", type=str, default=shared.DATA_PATH, help="Path to data directory")
parser.add_argument("--token", type=str, default=None, help="Token address to extract features")
parser.add_argument("--to_block", type=int, default=shared.BLOCKSTUDY, help="To block")
args = parser.parse_args()

data_path = args.data_path
token_list = args.token
to_block = args.to_block

# FROM PAPER: "If more than one month has passed between the last movement 
# or transaction of the token so far, we consider that the token is inactive"

# Load the data


tokens = pd.read_csv(data_path + "/tokens.csv")
if token_list is not None:
    tokens = tokens[tokens['token_address'] == token_list]
# print(token_list)
print("Extracting transfer heuristics for ", len(tokens), " tokens.")
active_transfer_dict = {"token_address": [], "inactive_transfers": []}

for token in tokens['token_address']:
    active_transfer_dict["token_address"].append(token)
    try:
        transfers = pd.read_csv(data_path + "/" + token + ".csv", iterator=True, chunksize=1000, index_col=0)
        max_block = 0
        for transfer in transfers:
            cur_max = transfer['block_number'].max()
            if cur_max > max_block:
                max_block = cur_max
        # check if there are any transfers in the last month
        # MIDDLE SSHOULD BE LIKE: 19097239
        last_transfer = transfer
        if last_transfer < to_block - shared.BLOCKS_TO_BE_INACTIVE:
            active_transfer_dict["inactive_transfers"].append(1)
        else:
            active_transfer_dict["inactive_transfers"].append(0)
    except FileNotFoundError:
        active_transfer_dict["inactive_transfers"].append(1)
        # print("No transfer data for token: ", token)

df = pd.DataFrame(active_transfer_dict, index=active_transfer_dict["token_address"])
# print(active_transfer_dict)
try:
    df_old = pd.read_csv(data_path+"/transfer_heuristics.csv", index_col="token_address")
    # print("df_old: ", df_old)
    if df_old.index.isin(df.index).any():
        df_old = df_old[~df_old.index.isin(df.index)]
    df = pd.concat([df_old, df], ignore_index=True)
except FileNotFoundError:
    pass
print("df looks like: ")
df.to_csv(data_path+"/transfer_heuristics.csv", index=False)
print("Saved transfer heuristics to ", data_path+"/transfer_heuristics.csv.")
print("Finished transfer heuristics.")