import configparser
import subprocess
from web3 import Web3

def init():

    global INFURA_URL_INDEX
    global INFURA_URLS
    global USE_POOL_INFURA
    global USE_WALLET_INFURA
    global API_KEY
    global UNISWAP_FACTORY
    global SUSHISWAP_FACTORY
    global UNILOCK_ADDRESS
    global EXCHANGES
    global ETH_ADDRESS
    global DEAD_ADDRESS
    global WETH
    global TOKEN_TOLERANCE
    global POOLS
    global FAKE_POOL
    global MULTICALL_CONTRACT
    global TRANSACTION
    
    global ROOT_FOLDER
    global WEEK
    global ABI
    global ABI_FACTORY
    global BLOCKSTUDY
    global BLOCKSTUDY_FROM
    global DATA_PATH
    global ABI_POOL
    global BLOCKS_PER_DAY
    global BLOCKS_TO_BE_INACTIVE
    
    global web3
    global multicall

    ROOT_FOLDER        = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=True, universal_newlines=True, stdout=subprocess.PIPE).stdout.strip()
    config = configparser.ConfigParser()
    config.read(ROOT_FOLDER + "/config.ini")

    # # Get infura node url and logic booleans
    INFURA_URL_INDEX  = 0
    INFURA_URLS       = [config.get("NODE", "INFURA_URL_0"), config.get("NODE", "INFURA_URL_1")]
    USE_POOL_INFURA    = config.getboolean("NODE", "USE_POOL_INFURA")
    USE_WALLET_INFURA  = config.getboolean("NODE", "USE_WALLET_INFURA")
    
    # Get etherscan keys
    API_KEY            = config.get("APIS", "ETHERSCAN_API_KEY")

    # Get tokens addresses
    ETH_ADDRESS        = config.get("ADDRESS", "ETH_ADDRESS")
    DEAD_ADDRESS       = config.get("ADDRESS", "DEAD_ADDRESS")
    WETH               = config.get("ADDRESS", "WETH_ADDRESS")
    MULTICALL_CONTRACT = config.get("ADDRESS", "MULTICALL_CONTRACT")

    # Get routers addresses
    UNISWAP_ADDRESS    = config.get("ROUTERS", "UNISWAP_ADDRESS")
    UNILOCK_ADDRESS    = config.get("ADDRESS", "UNILOCK_ADDRESS")
    SUSHISWAP_ADDRESS  = config.get("ROUTERS", "SUSHISWAP_ADDRESS")
    FAKE_POOL          = config.get("POOLS", "FAKE_POOL")

    # Get pools factories
    UNISWAP_FACTORY    = config.get("FACTORIES", "UNISWAP_FACTORY")

    #Get log hashes
    TRANSACTION        = config.get("LOG_HASHES","TRANSACTION")

    EXCHANGES          = {
        "uniswap": UNISWAP_ADDRESS.lower(),
        "sushiswap": SUSHISWAP_ADDRESS.lower()
    }
    
    TOKEN_TOLERANCE    = float(config.get("THRESHOLDS", "TOKEN_TOLERANCE"))
    # Define other globals not saved in config.ini
    WEEK               = 4*60*24*7
    ABI                = open(ROOT_FOLDER + "/ABIs/normal_token_abi.txt").read()
    ABI_FACTORY        = open(ROOT_FOLDER + "/ABIs/factory_abi.txt").read()
    ABI_POOL           = open(ROOT_FOLDER + "/ABIs/abi_pool.txt").read()
    # Define global objects
    BLOCKS_PER_DAY    = 7500
    BLOCKSTUDY_FROM   = 10522038 #10822038
    BLOCKSTUDY        = 13152303
    BLOCKS_TO_BE_INACTIVE  =  BLOCKS_PER_DAY *30

    DATA_PATH = "./data_mine"

    web3 = Web3(Web3.HTTPProvider(INFURA_URLS[INFURA_URL_INDEX]))
    # multicall =  Multicall(web3.eth)
