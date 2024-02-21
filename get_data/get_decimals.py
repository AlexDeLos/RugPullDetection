import shared
shared.init()


def get_decimal_token(token_address):
    """
    Gets token decimal given a token address.

    Parameters
    ----------
    token_address: str
        String containing token address.

    Returns
    -------
    decimal: int
        Int corresponding to token decimal.
    """

    contract = shared.web3.eth.contract(token_address, abi=shared.ABI)
    # 0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f
    try:
        decimals = contract.functions.decimals().call()
    except:
        decimals = -999
        print(f"Error getting decimals for {token_address}")

    return decimals
