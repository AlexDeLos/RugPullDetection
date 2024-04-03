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
    print("transfers = pd.DataFrame(transfers)")
    transfers = pd.DataFrame(transfers)
    print("from_, to_, values = 2, 3, 4")
    from_, to_, values = 2, 3, 4
    print("num_transactions_list = len(transfers)")
    num_transactions_list = len(transfers)
    print("n_unique_addresses = len(set(transfers[from_].tolist() + transfers[to_].tolist()))")
    n_unique_addresses = len(set(transfers[from_].tolist() + transfers[to_].tolist()))
    print("G = nx.Graph()")
    G = nx.Graph()
    print("transfers = transfers.iloc[:10000]")
    transfers = transfers.iloc[:10000]
    print("for From, To, Value in zip(transfers[from_], transfers[to_], transfers[values]):")
    for From, To, Value in zip(transfers[from_], transfers[to_], transfers[values]):
       print("G.add_edge(From, To, weight=Value)")
       G.add_edge(From, To, weight=Value)
    try:
        print("cluster_coeffs = nx.average_clustering(G)")
        cluster_coeffs = nx.average_clustering(G)
    except:
        print("cluster_coeffs = 0")
        cluster_coeffs = 0
    print("features = {")
    features = {
        'num_transactions': num_transactions_list,
        'n_unique_addresses': n_unique_addresses,
        'cluster_coeff': cluster_coeffs
    }
    print("return features")
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
    from_, to_, values = 2, 3, 4
    total_supply, total_supply_ans = 0, 0

    for i in range(len(transfers)):
        balances[transfers[i][from_]] -= float(transfers[i][values])
        balances[transfers[i][to_]] += float(transfers[i][values])
        if transfers[i][from_] == shared.ETH_ADDRESS:
            total_supply += float(transfers[i][values])
            balances[transfers[i][from_]] = 0
        if transfers[i][to_] == shared.ETH_ADDRESS:
            total_supply -= float(transfers[i][values])
            balances[transfers[i][to_]] = 0
    if total_supply != 0:
        curve = distribution_metric(balances, total_supply)
    else:
        curve = 1
    return {'tx_curve': curve}



