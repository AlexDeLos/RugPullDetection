# RugPullDetection

### Notes
The main task is the generation of the data to be used in training. This is done by the build_data.py file in a nohup process.
#### nohup informantion
We use nohup so that we can close the terminal and the code continues to run in the instance. The command structure is the following: "nohup python nohup python3 example_run.py --example flag > example.out". At time of writting the current runing command is: "nohup python nohup python3 build_data.py -e True -t True --data_path full_data_2 > example.out"".
Running this will produce to output files, a .out file (focus on this one, it will show all the prints) and a .log file.

#### code flags
For build_data.py the flags are:
 - --data_path: this is the most important flag, it determines where the data is saved, this by default is "./data_run_2" but it is currently running with value "full_data_2".
 - --pools: Boolean flag that determines if the pools and tokens should be extracted again. Should really only be ran if you change the shared.BLOCKSTUDY_FROM and shared.BLOCKSTUDY values.
 - --events: Determines if the events should be collected again.
 - --token_tx: Determines if the transfer events should be collected again.

 Other flags of note:
 - --token: this flag is to be used when testing the fully trained model, please ignore it.
#### Important files
 - data/healthy_tokens.cvs: this file need to be present in to data folder and need to be added manually.
 - build_data.py: This generates the following files: "pool_sync_events/pool.json", "pool_transfer_events/pool.json", "decimals.csv", "pool_dict.json", "pools_of_token.json", "tokens.csv".
 - ML/Labelling/assing_label.py: creates the "labeled_list.py"
#### Important folders
- ML/Labelling -> has all the functions to create the labels.csv file
#### Trouble shooting steps
- If the instance crashed then make the step veriable in the build_data.py file smaller
- Check the running precesses. with "ps wx"
- If the process is no longer running check the logs to see why it stopped
- Check the logs -> if it is a normal python error then just fix it.
-  If "extract_transfer_heuristics ran" has been printed at the end then it finished -> check the data_path folder to make sure the JSONs and cvs files look good.

#### What to do when it is done
- Attempt to run the "assign_label.py" file with the proper --data_path flag and NO TOKEN FLAG. -> this should make a "labeled_list.csv" file
- The attempt to run "build_dataset.py" -> this should generate a "X.csv" file
- Feel free to try and run train the model now, but you have done all that I expected :)


### Introduction

In this repository we will find the necessary tools to replicate the work made in [Do not rug on me](https://arxiv.org/abs/2201.07220). This repository, allows to download all the necessary data of UniswapV2 pools in the Ethereum blockchain. That is, all the PairPools, with their liquidity, prices and Add/remove events, all the source codes of the tokens,...
Moreover, in the folder ML we will find the tools to predict with high accurracy and sensibility if a token will eventually become a scam/rug or not.

### Abstract

Uniswap, like other DEXs, has gained much attention this year because it is a non-custodial and publicly verifiable exchange that allows users to trade digital assets without trusted third parties. However, its simplicity and lack of regulation also makes it easy to execute initial coin offering scams by listing non-valuable tokens. This method of performing scams is known as rug pull, a phenomenon that already existed in traditional finance but has become more relevant in DeFi. Various projects such as [TokenSniffer](https://tokensniffer.com/) have contributed to detecting rug pulls in EVM compatible chains. However, the first longitudinal and academic step to detecting and characterizing scam tokens on Uniswap was made in [Trade or Trick? Detecting and Characterizing Scam Tokens on Uniswap Decentralized Exchange](https://arxiv.org/pdf/2109.00229.pdf). The authors collected all the transactions related to the Uniswap V2 exchange and proposed a machine learning algorithm to label tokens as scams. However, the algorithm is only valuable for detecting scams accurately after they have been executed. This paper increases their data set by 20K tokens and proposes a new methodology to label tokens as scams. After manually analyzing the data, we devised a theoretical classification of different malicious maneuvers in Uniswap protocol. We propose various machine-learning-based algorithms with new relevant features related to the token propagation and smart contract heuristics to detect potential rug pulls before they occur. In general, the models proposed achieved similar results. The best model obtained an accuracy of 0.9936, recall of 0.9540, and precision of 0.9838 in distinguishing  non-malicious tokens from scams prior to the malicious maneuver.

### Requirements

- scikit-learn
- web3py
- beautifulsoup4
- pandas
- numpy

### How to use it

<!-- As mentioned in the paper, we highly recommend to have access to a full or an archive node to download all the necesary data, and add the endpoint in config.ini. -->

0. Make sure to modify the config.ini file with the necessary information and change the values in the shared file appropriately.
1. Run the scripts in get_data in the following order:
  1.1 get_tokens_and_pools.py ->Done
  1.2 get_pool_events.py ->Done
  1.3 get_contract_creation.py ->Done and saved in a csv file
  1.4 get_decimals.py ->Done
  1.5 get_source_code.py -> DONE
  1.6 get_transfers.py -> DONE
3. Run the extract pool_heuristics.py to extract the features of the pools.
4. Run the extract extract_transfer_heuristics.py to extract the features of the tokens.
5. Run assign_labels.py to label the tokens.
6. Run the build_dataset.py to build the dataset.
7. ML.
8. Jupyter Notebook.


### Example


### Results


### Reference

- [Do not rug on me](https://arxiv.org/abs/2201.07220)




