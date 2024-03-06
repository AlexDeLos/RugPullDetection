import sys
import pandas as pd
import os
import argparse
sys.path.append(os.getcwd())
import shared
shared.init()


parser = argparse.ArgumentParser()
parser.add_argument("--data_path", type=str, default=shared.DATA_PATH, help="Path to data directory")
parser.add_argument("--token", type=str, default=None, help="Token address to extract features")
args = parser.parse_args()

data_path = args.data_path
token = args.token
# FROM PAPER: "If more than one month has passed between the last movement 
# or transaction of the token so far, we consider that the token is inactive"

# Load the data


tokens = pd.read_csv(shared.DATA_PATH + "/tokens.csv")
if token is not None:
    tokens = tokens[tokens['token_address'] == token]

active_transfer_dict = {"token_address": [], "inactive_transfers": []}

for token in tokens['token_address']:
    active_transfer_dict["token_address"].append(token)
    try:
        transfers = pd.read_csv(shared.DATA_PATH + "/Token_tx/" + token + ".csv")
        # check if there are any transfers in the last month
        # MIDDLE SSHOULD BE LIKE: 19097239
        last_transfer = transfers['block_number'].max()
        if last_transfer < shared.BLOCKSTUDY - shared.BLOCKS_TO_BE_INACTIVE:
            active_transfer_dict["inactive_transfers"].append(1)
        else:
            active_transfer_dict["inactive_transfers"].append(0)
    except FileNotFoundError:
        active_transfer_dict["inactive_transfers"].append(1)
        print("No transfer data for token: ", token)

df = pd.DataFrame(active_transfer_dict)
df.to_csv(data_path+"/transfer_heuristics.csv", index=False)
print("Finished transfer heuristics.")