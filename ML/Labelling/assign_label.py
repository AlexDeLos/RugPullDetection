import pandas as pd
import sys
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


df_pool = pd.read_csv(data_path + "/pool_heuristics.csv", index_col="token_address")
df_transfers = pd.read_csv(data_path + "/transfer_heuristics.csv").drop_duplicates(subset=['token_address'])
df_transfers = df_transfers.set_index("token_address")
label_list = []

df = pd.concat([df_transfers, df_pool], axis=1, join='inner')
df['inactive'] = df['inactive'] * df['inactive_transfers']
df = df.drop(['inactive_transfers'], axis=1)
# print out the data frame
print(df)

if token is None:
    healthy_tokens = pd.read_csv(data_path+ "/healthy_tokens.csv")['token_address']
else:
    healthy_tokens = []

for token in healthy_tokens:
    try:
        label_list.append([token, df_pool.loc[token]['pool_address'], 1, 0])
    except:
        pass

#? what makes it type 1 or 2?
df_inactius = df.loc[(df["inactive"] == 1) & (df['late_creation'] == 0)]
rug_pull    = df_inactius.loc[(df_inactius["liq_MDD"] == -1)]
rug_pull_1  = rug_pull.loc[rug_pull['liq_RC'] <= 0.2]
print("rug_pull_1: ", rug_pull_1)
for token in rug_pull_1.index:
    label_list.append([token, df_pool.loc[token]['pool_address'], 0, 1])

df_inactius = df.loc[(df["inactive"] == 1) & (df['late_creation'] == 0)]
rug_pull    = df_inactius.loc[(df_inactius["liq_MDD"] == 0)]
rug_pull    = rug_pull.loc[(rug_pull['price_MDD'] >= -1) & (rug_pull['price_MDD'] <= -0.9)]
rug_pull_2  = rug_pull.loc[(rug_pull['price_RC'] >= 0) & (rug_pull['price_RC'] <= 0.01)]

print("rug_pull_2: ", rug_pull_2)

for token in rug_pull_2.index:
    label_list.append([token, df_pool.loc[token]['pool_address'], 0, 2])

pd.DataFrame(label_list, columns=["token_address", "pool_address", "label", "type"]).to_csv(data_path+"/labeled_list.csv", index=False)
print("DONE!")