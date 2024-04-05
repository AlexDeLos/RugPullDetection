import networkx as nx
from collections import defaultdict

import pandas as pd

import shared
shared.init()


def get_transfer_features(transfers):
    """
    Computes features based on token transfers.

    Parameters
    ----------
    transfers: Dataframe
        Dataframe with columns: "transactionHash", "block_number", "from", "to", "value".

    Returns
    -------
    features: Dict[str, float]
        Dictionary that contains all computed features.
    """
    if not isinstance(transfers, pd.DataFrame):
        transfers = pd.DataFrame(transfers)
    num_transactions_list = len(transfers)
    n_unique_addresses = transfers[['from', 'to']].stack().nunique()
    G = nx.Graph()
    #? Que passa si no fem això? com funciona amb més de 10000?
    transfers = transfers.iloc[:10000]
    print('starting to add edges')
    count = 0
    max = len(transfers['from'])
    for From, To, Value in zip(transfers['from'], transfers['to'], transfers['value']):
       print(f'Adding edge{count}/{max}')
       count += 1
       G.add_edge(From, To, weight=Value)
    try:
        cluster_coeffs = nx.average_clustering(G)
    except:
        cluster_coeffs = 0
    features = {
        'num_transactions': num_transactions_list,
        'n_unique_addresses': n_unique_addresses,
        'cluster_coeff': cluster_coeffs
    }
    return features


def distribution_metric(balances, total_supply):
    """ HHIndex actual computation"""
    g1 = sum([(value/total_supply)**2 for holder,value in balances.items()
              if holder not in [shared.ETH_ADDRESS,shared.DEAD_ADDRESS]])
    return g1


def get_curve(transfers):
    """
    Computes HHIndex.

    Parameters
    ----------
    transfers: Dataframe
        Dataframe with columns: "transactionHash", "block_number", "from", "to", "value".
    Returns
    -------
    Dictionary that contains the computed HHI
    """

    balances = defaultdict(lambda: 0)
    total_supply, total_supply_ans = 0, 0

    # TODO: transfers[i] only works in list, that is inefficient. change it to .loc df
    for i in range(len(transfers)):
        balances[transfers.iloc[i]['from']] -= float(transfers.iloc[i]['value'])
        balances[transfers.iloc[i]['to']] += float(transfers.iloc[i]['value'])
        if transfers.iloc[i]['from'] == shared.ETH_ADDRESS:
            total_supply += float(transfers.iloc[i]['value'])
            balances[transfers.iloc[i]['from']] = 0
        if transfers.iloc[i]['to'] == shared.ETH_ADDRESS:
            total_supply -= float(transfers.iloc[i]['value'])
            balances[transfers.iloc[i]['to']] = 0
    if total_supply != 0:
        curve = distribution_metric(balances, total_supply)
    else:
        curve = 1
    return {'tx_curve': curve}



