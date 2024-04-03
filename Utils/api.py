import requests
from web3.datastructures import AttributeDict
from hexbytes import HexBytes
import sys
import time
import logging
import warnings
import ast
sys.path.append("../")
import shared
shared.init()


def get_rpc_response(method, list_params=[]):
    """
    Parameters
    ----------
    method: str
        Indicates node method.
    list_params: List[Dict[str, Any]]
        List of request parameters.

    Returns
    -------
    args_event: AttributeDict
        Change number basis.

    Example
    -------
        If we want token transfers of 0xa150Db9b1Fa65b44799d4dD949D922c0a33Ee606
        between blocks [11000000, 11025824] then:
        method: 'eth_getLogs'
        list_params: [[{'address': '0xa150Db9b1Fa65b44799d4dD949D922c0a33Ee606',
                    'fromBlock': '0xa7d8c0', 'toBlock': '0xa83da0',
                    'topics': ['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef']}]]
    """
    url_index = shared.INFURA_URL_INDEX
    urls = shared.INFURA_URLS
    url = urls[url_index]
    list_params = list_params or []
    data = [{"jsonrpc": "2.0", "method": method, "params": params, "id": 1} for params in list_params]
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=data)
    logs = response.json()
    old_log = logs.copy()
    results = [ [] for _ in range(len(logs)) ]
    to_pop = []
    count = 0
    for j, log in enumerate(old_log):
        if list(log.keys())[-1] == "error":
            logging.debug(f"Error in log {j}: {log['error']}")
            if log['error']['code'] == -32005:
                if log['error']['message'].split('.')[0] == 'query returned more than 10000 results':
                    # drop the ' ', '[', and ',' characters
                    from_block_new = log['error']['data']['from']
                    to_block_new = log['error']['data']['to']
                    from_block_old = list_params[j][0]["fromBlock"]
                    step_size = ast.literal_eval(to_block_new) - ast.literal_eval(from_block_new)
                    from_block_new = from_block_old
                    # let's query in smaller steps
                    to_pop.append(j)
                    new_list_params = list_params[j][0].copy()
                    while ast.literal_eval(to_block_new) < ast.literal_eval(list_params[j][0]["toBlock"]):
                        to_block_new = hex(step_size + ast.literal_eval(from_block_new))
                        new_list_params['fromBlock'] = from_block_new
                        new_list_params['toBlock'] = to_block_new
                        res = get_rpc_response(method, [[new_list_params]])
                        for i in res:
                            if i['result'] != []:
                                results[j].append(i)
                        from_block_new = hex(step_size + ast.literal_eval(from_block_new))
                elif log['error']['message'].split('.')[0] == 'project ID request rate exceeded':
                    warnings.warn('exceeded rate limit, waiting 30 seconds')
                    logging.warning('exceeded rate limit, waiting 30 seconds')
                    time.sleep(30)
                    return get_rpc_response(method, list_params)
                else:
                    logging.warning("change infura url to another one, this one is not working anymore wait 24h?")

                    warnings.warn("change infura url to another one, this one is not working anymore wait 24h?")
                    url_index= url_index + 1
                    url_index = url_index % len(urls)
                    shared.INFURA_URL_INDEX = url_index
                    count = count + 1
                    if count < len(urls) +1:
                        return get_rpc_response(method, list_params, url_index)
                    else:
                        logging.error("No URLS available")
                        raise Exception("No URLS available")
                    
            else:
                count = 0
                
    count = 0
    for j in to_pop:
        logs.pop(j-count)
        count += 1
    
    for n, res in enumerate(results):
        for i in res:
            logs.insert(n,i)
    return logs

def change_log_dict(log_dict):
    """
    Parameters
    ----------
    log_dict: AttributeDict
        Decoded logs.

    Returns
    -------
    args_event: AttributeDict
        Change number basis.
    """
    dictionary = log_dict.copy()
    dictionary['blockHash'] = HexBytes(dictionary['blockHash'])
    dictionary['blockNumber'] = int(dictionary['blockNumber'], 16)
    dictionary['logIndex'] = int(dictionary['logIndex'], 16)
    for i in range(len(dictionary['topics'])):
        dictionary['topics'][i] = HexBytes(dictionary['topics'][i])
    dictionary['transactionHash'] = HexBytes(dictionary['transactionHash'])
    dictionary['transactionIndex'] = int(dictionary['transactionIndex'], 16)
    return AttributeDict(dictionary)


def clean_logs(contract, myevent, log):
    """
    Parameters
    ----------
    contract: web3.eth.contract
        Contract that contains the event.
    myevent: str
        string with event name.
    log: List[AttributeDict]
        List containing raw node response.

    Returns
    -------
    args_event: AttributeDict
        Decoded logs.
    """
    logging.debug(f"Cleaning logs for event {myevent} on contract {contract.address}")
    log_dict = AttributeDict({'logs': log})
    ret = []
    eval_string = 'contract.events.{}().processReceipt({})'.format(myevent, log_dict)
    try:
        # suppress user warnings here
        args_event = eval(eval_string)
        args_event = args_event[0]
    except IndexError as e:
        args_event = None
    return args_event

def get_logs(contract, myevent, hash_create, from_block, to_block, number_batches):
    """
    Get event logs using recursion.

    Parameters
    ----------
    contract: web3.eth.contract
        Contract that contains the event.
    myevent: str
        string with event name.
    hash_create: str
        hash of the event.
    from_block: int
        Starting block.
    to_block: int
        Ending block.
    number_batches: int
        infura returns just 10k logs each call, therefore we need to split time series into batches.

    Returns
    -------
    events_clean: list
        List with all clean logs.
    """

    events_clean = []
    block_list = [int(from_block + i * (to_block - from_block) / number_batches) for i in range(0, number_batches)] + [
        to_block]

    block_list[0] -= 1
    if hash_create is None:
        list_params = [[{"address": contract.address,
                     "fromBlock": hex(block_list[i - 1] + 1),
                     "toBlock": hex(block_list[i])
                     }] for i in range(1, number_batches + 1)
                     ]
    else:
        list_params = [[{"address": contract.address,
                        "fromBlock": hex(block_list[i - 1] + 1),
                        "toBlock": hex(block_list[i]),
                        "topics": [hash_create]
                        }] for i in range(1, number_batches + 1)
                        ]

    logs = get_rpc_response("eth_getLogs", list_params)
    logging.debug(f"From block: {from_block}, to block: {to_block}, number of logs: {len(logs)}")
    for j, log in enumerate(logs):
        if list(log.keys())[-1] == "result":
            for event in log['result']:
                #NEVER IN HERE CAUSE LOGS ARE EMPTY
                log_dict = change_log_dict(event)
                if type(myevent) == list:
                    for event in myevent:
                        kl = clean_logs(contract, event, [log_dict])
                        if kl is not None:
                            events_clean += [kl]
                else:
                    events_clean += [clean_logs(contract, myevent, [log_dict])]
        elif list(log.keys())[-1] == "error":
            if log['error']['code'] == -32005:
                #wait for 30 seconds
                if log['error']['message'].split('.')[0] != 'query returned more than 10000 results':
                    testsdsd= ''
                time.sleep(30)
                warnings.warn("change infura url to another one, this one is not working anymore wait 24h")
                raise Exception("change infura url to another one, this one is not working anymore wait 24h")
            
            else:
                print(log['error'])
                return []
        else:
            events_clean += get_logs(contract, myevent, hash_create, int(list_params[j][0]["fromBlock"], 16),
                                     int(list_params[j][0]["toBlock"], 16), number_batches) #chage number_batches to 10
    # remove None values
    events_clean = [x for x in events_clean if x is not None]
    return events_clean
