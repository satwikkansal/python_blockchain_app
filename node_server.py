from hashlib import sha256
import json
from json import JSONEncoder

import time
import threading

from flask import Flask, request
import requests
import os

backup_path = "./backup"

transaction_fields = {"YEAR", "DAY_OF_WEEK", "FL_DATE", "OP_CARRIER_AIRLINE_ID",
"OP_CARRIER_FL_NUM", "ORIGIN_AIRPORT_ID", "ORIGIN", "ORIGIN_CITY_NAME", "ORIGIN_STATE_NM", "DEST_AIRPORT_ID",
"DEST", "DEST_CITY_NAME", "DEST_STATE_NM", "DEP_TIME", "DEP_DELAY", "ARR_TIME", "ARR_DELAY", "CANCELLED", "AIR_TIME"}

class Transaction:
    id = 0

    def __init__(self, transaction):
        self.TRANSACTION_ID = Transaction.id

        #debug
        print("AAAAAA")
        print(self.__dict__)
        print("BBBBBBB")
        print(transaction)
        #


        self.__dict__.update(transaction)
        Transaction.id += 1


def write_block_and_check_dir(block, id):

    if(not os.path.isdir(backup_path)):
        try:
            os.mkdir(backup_path)
        except OSError:
            print ('Creation of the directory %s failed!' % backup_path)
            return False
        else:
            print ("Successfully created the directory %s" % backup_path)

    f = open('{}/{}'.format(backup_path, id), 'w')
    f.write(json.dumps(block, cls=BlockEncoder, sort_keys=True))
    f.close()
    return True

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        """
        A function that return the hash of the block contents.
        """
        block_string = json.dumps(self, cls=BlockEncoder, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    def has_transaction(id):
        return self.transactions[0].id <= id and self.transactions[-1].id >= id

    def get_transaction(id):
        if(self.has_transaction(id)):
            return self.transactions[id - self.transactions[0].id]
        else:
            return False

# subclass JSONEncoder
class BlockEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__

class Blockchain:
    # difficulty of our PoW algorithm
    difficulty = 2

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block(0, [], 0, "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of latest block
          in the chain match.
        """
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    @staticmethod
    def proof_of_work(block):
        """
        Function that tries different values of nonce to get a hash
        that satisfies our difficulty criteria.
        """
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "0"

        for block in chain:
            block_hash = block.hash
            # remove the hash field to recompute the hash again
            # using `compute_hash` method.
            delattr(block, "hash")

            if not cls.is_valid_proof(block, block_hash) or \
                    previous_hash != block.previous_hash:
                result = False
                break

            block.hash, previous_hash = block_hash, block_hash

        return result

    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out Proof Of Work.
        """
        if not self.unconfirmed_transactions:
            return -1

        unconfirmed_transactions_to_block = []

        if len(self.unconfirmed_transactions) > 1000:
            unconfirmed_transactions_to_block = self.unconfirmed_transactions[0:1000]
            self.unconfirmed_transactions = self.unconfirmed_transactions[1000:]
        else:
            unconfirmed_transactions_to_block = self.unconfirmed_transactions
            self.unconfirmed_transactions = []

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=unconfirmed_transactions_to_block,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        if(write_block_and_check_dir(new_block, new_block.index)):
            return 1
        else:
            print("Save failed!")
            return 0

    def get_block(id):
        return self.chain[id]

    #read from the backup folder and initialize the chain
    def read_backup(self):
        if(not os.path.isdir(backup_path)):
            return False
        for r, d, f, in os.walk(backup_path):
            backup = f                          #list of the names of the files in the backup folder
        backup.sort()

        for n in backup:
            tmp_file = open(backup_path + '/' + n, 'r')
            tmp_json = tmp_file.read()





app = Flask(__name__)

# the node's copy of blockchain
blockchain = Blockchain()
blockchain.create_genesis_block()
#blockchain.read_backup()

# the address to other participating members of the network
peers = set()

# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    #required_fields = ["author", "content"]
    global transaction_fields

    for field in transaction_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404

    tx_data["timestamp"] = time.time()

    transaction = Transaction(tx_data)
    blockchain.add_new_transaction(transaction)

    return "Success", 201


# endpoint to return the node's copy of the chain.
# Our application will be using this endpoint to query
# all the posts to display.
@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:


        block_to_add = block.__dict__.copy()

        #debug
        print("BLOCK BEFORE")
        print(block_to_add)
        #

        transactions_dict = []
        for i in range(0,len(block_to_add["transactions"])):
            print("POS")
            print(i)
            print(block_to_add["transactions"][i].__dict__)
            transactions_dict.append(block_to_add["transactions"][i].__dict__)
            #block_to_add["transactions"][i] = block_to_add["transactions"][i].__dict__

        block_to_add["transactions"] = transactions_dict

        #debug
        print("BLOCK AFTER")
        print(block_to_add)
        #

        chain_data.append(block_to_add)

    #debug
    print("CHAIN_DATA")
    print(type(chain_data))
    print(chain_data)
    #

    return json.dumps({"length": len(chain_data),
                       "chain": chain_data,
                       "peers": list(peers)}, cls=BlockEncoder)

# endpoint to return the transactions of a block gived its id.
# Our application will be using this endpoint to query
# all the posts to display.
@app.route('/blocks/<block_id>', methods=['GET'])
def get_transaction_by_block_id(block_id):
    block = blockchain.get_block(block_id)
    return json.dumps({"length": len(block.transactions),
                       "transactions": block.transactions})

# endpoint to return the transaction gived its id.
# Our application will be using this endpoint to query
# all the posts to display.
@app.route('/transactions/<transaction_id>', methods=['GET'])
def get_transaction_by_id(transaction_id):
    min_id = 0
    max_id = len(blockchain) - 1
    med_id = max_id // 2
    med_block = blockchain.get_block(med_id)

    while(not med_block.has_transaction(transaction_id) and min_id != max_id):
        if(transaction_id < med_block.transactions[0].id):
            max_id = med_id
        else:
            min_id = med_id
        med_id = (max_id + min_id) // 2
        med_block = blockchain.get_block(med_id)

    if(med_block.has_transaction(transaction_id)):
        return med_block.get_transaction(transaction_id)
    else:
        return False



# endpoint to request the node to mine the unconfirmed
# transactions (if any). We'll be using it to initiate
# a command to mine from our application itself.
@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if result == -1:
        return "No transactions to mine"
    elif result == 0:
        return 500, "No transactions to mine"
    else:
        # Making sure we have the longest chain before announcing to the network
        chain_length = len(blockchain.chain)
        consensus()
        if chain_length == len(blockchain.chain):
            # announce the recently mined block to the network
            announce_new_block(blockchain.last_block)
        return "Block #{} is mined.".format(blockchain.last_block.index)


# endpoint to add new peers to the network.
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    peers.add(node_address)

    # Return the consensus blockchain to the newly registered node
    # so that he can sync
    return get_chain()


@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    """
    Internally calls the `register_node` endpoint to
    register current node with the node specified in the
    request, and sync the blockchain as well as peer data.
    """
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remote node and obtain information
    response = requests.post(node_address + "/register_node",
                             data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        global blockchain
        global peers
        # update chain and the peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        return "Registration successful", 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code


def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0:
            continue  # skip genesis block
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"])
        proof = block_data['hash']
        added = generated_blockchain.add_block(block, proof)
        if not added:
            raise Exception("The chain dump is tampered!!")
    return generated_blockchain


# endpoint to add a block mined by someone else to
# the node's chain. The block is first verified by the node
# and then added to the chain.
@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["nonce"])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


# endpoint to query unconfirmed transactions
@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)


def consensus():
    """
    Our naive consnsus algorithm. If a longer valid chain is
    found, our chain is replaced with it.
    """
    global blockchain

    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        response = requests.get('{}chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True

    return False


def announce_new_block(block):
    """
    A function to announce to the network once a block has been mined.
    Other blocks can simply verify the proof of work and add it to their
    respective chains.
    """
    for peer in peers:
        url = "{}add_block".format(peer)
        headers = {'Content-Type': "application/json"}
        requests.post(url,
                      data=json.dumps(block.__dict__, sort_keys=True),
                      headers=headers)

# Uncomment this line if you want to specify the port number in the code
def start_runner():
    def start_loop():
        while True:
            print('In start loop ', threading.current_thread().ident)
            try:
                r = requests.get('http://127.0.0.1:8000/mine')
                if r.status_code == 200:
                    print(r.content)
                print(r.status_code)
            except:
                print('Server not yet started')
            time.sleep(60)

    print('Started runner')
    thread = threading.Thread(target=start_loop)
    thread.start()

start_runner()
app.run(debug=False, port=8000)
