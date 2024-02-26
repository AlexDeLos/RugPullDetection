# RugPullDetection


### TODO
- Notebooks: Labels, Missing analysis, Features_track, Interpretability.

### Introduction

In this repository we will find the necessary tools to replicate the work made in [Do not rug on me](https://arxiv.org/abs/2201.07220). This repository, allows to download all the necessary data of UniswapV2 pools in the Ethereum blockchain. That is, all the PairPools, with their liquidity, prices and Add/remove events, all the source codes of the tokens,...
Moreover, in the folder ML we will find the tools to predict with high accurracy and sensibility if a token will eventually become a scam/rug or not.

### Abstract

Uniswap, like other DEXs, has gained much attention this year because it is a non-custodial and publicly verifiable exchange that allows users to trade digital assets without trusted third parties. However, its simplicity and lack of regulation also makes it easy to execute initial coin offering scams by listing non-valuable tokens. This method of performing scams is known as rug pull, a phenomenon that already existed in traditional finance but has become more relevant in DeFi. Various projects such as [TokenSniffer](https://tokensniffer.com/) have contributed to detecting rug pulls in EVM compatible chains. However, the first longitudinal and academic step to detecting and characterizing scam tokens on Uniswap was made in [Trade or Trick? Detecting and Characterizing Scam Tokens on Uniswap Decentralized Exchange](https://arxiv.org/pdf/2109.00229.pdf). The authors collected all the transactions related to the Uniswap V2 exchange and proposed a machine learning algorithm to label tokens as scams. However, the algorithm is only valuable for detecting scams accurately after they have been executed. This paper increases their data set by 20K tokens and proposes a new methodology to label tokens as scams. After manually analyzing the data, we devised a theoretical classification of different malicious maneuvers in Uniswap protocol. We propose various machine-learning-based algorithms with new relevant features related to the token propagation and smart contract heuristics to detect potential rug pulls before they occur. In general, the models proposed achieved similar results. The best model obtained an accuracy of 0.9936, recall of 0.9540, and precision of 0.9838 in distinguishing  non-malicious tokens from scams prior to the malicious maneuver.

### Requirements

- scikit-learn
- web3py
- beautifulsoup4

### How to use it

As mentioned in the paper, we highly recommend to have access to a full or an archive node to download all the necesary data, and add the endpoint in config.ini.

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
6. ML.
7. Jupyter Notebook.


### Example


### Results


### Reference

- [Do not rug on me](https://arxiv.org/abs/2201.07220)



