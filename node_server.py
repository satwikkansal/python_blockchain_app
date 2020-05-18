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
        #print("AAAAAA")
        #print(self.__dict__)
        #print("BBBBBBB")
        #print(transaction)
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

        ## TODO update with metadata
    def has_transaction(self, id):
        #debug
        #print("69 ID ", id)
        #print("LEN TRANSACTIONS ", len(self.transactions))
        #print("FIRST TRANSACTION ID ", self.transactions[0].TRANSACTION_ID)

        return self.transactions[0].TRANSACTION_ID <= id and self.transactions[-1].TRANSACTION_ID >= id

        ## TODO update with metadata
    def get_transaction(self, id):

        if(self.has_transaction(id)):
            return self.transactions[id - self.transactions[0].TRANSACTION_ID]
        else:
            return False

    def get_block_len(self):
        return len(self.transactions)


# subclass JSONEncoder
class BlockEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__

class TransactionEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__


'''
chain_metadata: [
    {
        index: id,
        block_size: int,
        first_transaction: id,
        last_transaction: id,
        hash: hash,
        nonce: int,
        previous_hash: hash
    }
]
'''
class Blockchain:
    # difficulty of our PoW algorithm
    difficulty = 2
    LAST_CACHE_SIZE = 80000
    RANDOM_CACHE_SIZE = 80000

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain_metadata = []
        self.chain_random_cache = {}
        self.chain_last_cache = {}
        self.n_transactions = 0

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block(0, [], 0, "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain_metadata.append({ "index": genesis_block.index, "block_size": 0, "first_transaction": None, "last_transaction": None, "hash": genesis_block.hash, "nonce": genesis_block.nonce, "previous_hash": None })
        #self.chain_cache[genesis_block.index] = genesis_block

    @property
    def last_block_metadata(self):
        return self.chain_metadata[-1]


    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of latest block
          in the chain match.
        """
        previous_hash = self.last_block_metadata["hash"]

        if previous_hash != block.previous_hash:
            #debug
            #print("PREVIOUS HASH ERROR ", block.index)
            #
            return False

        if not Blockchain.is_valid_proof(block, proof):
            #debug
            #print("PROOF NOT VALID ", block.index)
            #
            return False
        #debug
        #print("ADDING BLOCK ", block.index)
        #
        self.n_transactions += block.get_block_len()
        block.hash = proof
        self.chain_metadata.append({
            "index": block.index,
            "block_size": block.get_block_len(),
            "first_transaction": block.transactions[0].TRANSACTION_ID,
            "last_transaction": block.transactions[-1].TRANSACTION_ID,
            "hash": block.hash,
            "nonce": block.nonce,
            "previous_hash": block.previous_hash
        })

        if (self.LAST_CACHE_SIZE > 0):
            self.chain_last_cache[block.index] = block
            # check if self.chain_last_cache is too big
            blocks_to_remove = []
            remaining_transactions = self.LAST_CACHE_SIZE
            #find block that must be removed from the cache
            for i in reversed(list(chain_last_cache.keys())):
                if remaining_transactions <= 0:
                    blocks_to_remove.append(i)
                else:
                    remaining_transactions -= self.chain_last_cache[i].block_size

            for i in blocks_to_remove:
                del self.chain_last_cache[i]

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
        ## TODO update with metadata, only with multi peers
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

        last_block_metadata = self.last_block_metadata

        new_block = Block(index=last_block_metadata.index + 1,
                          transactions=unconfirmed_transactions_to_block,
                          timestamp=time.time(),
                          previous_hash=last_block_metadata.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        if(write_block_and_check_dir(new_block, new_block.index)):
            return 1
        else:
            #print("Save failed!")
            return 0


    def check_block_with_metadata(self, block, id):
        #check block with metadata
        ret = ( (block.index == self.chain_metadata[id]["index"]) and
            (block.get_block_len() == self.chain_metadata[id]["block_size"]) and
            (block.transactions[0].TRANSACTION_ID == self.chain_metadata[id]["first_transaction"]) and
            (block.transactions[-1].TRANSACTION_ID == self.chain_metadata[id]["last_transaction"]) and
            (block.hash == self.chain_metadata[id]["hash"]) and
            (block.nonce == self.chain_metadata[id]["nonce"]) and
            (block.previous_hash == self.chain_metadata[id]["previous_hash"]) )

        #check block hash
        tmp_proof = block.__dict__.pop("hash")
        ret = ret and self.is_valid_proof(block, tmp_proof)
        return ret


    def check_block_in_cache(self,id):
        return (id in self.chain_last_cache or id in self.chain_random_cache)


    def set_last_cache(self):
        id = self.chain_metadata[-1]["index"]
        remaining_transactions = min(self.LAST_CACHE_SIZE, self.n_transactions)
        new_last_cache = {}
        if (remaining_transactions > 0):
            tmp_block = self.read_block_from_backup(id)

            #checks block is the same with metadata
            if not self.check_block_with_metadata(tmp_block, id):
                return False
            new_last_cache[id] = tmp_block
            remaining_transactions -= new_last_cache[id].get_block_len()

        step_back = 1
        while (remaining_transactions > 0):
            previous_id = id-step_back
            #maybe useless check into the if
            #check if previous_id is valid
            if (previous_id >= 1 and previous_id < len(blockchain.chain_metadata)):
                #check if previous_block is already stored in random_cache (recycle it, don't need to read from disk)
                if (previous_id in self.chain_random_cache):
                    new_last_cache[previous_id] = self.chain_random_cache[previous_id]
                    remaining_transactions -= new_last_cache[previous_id].get_block_len()
                #check if previous_block is already stored in last_cache (recycle it, don't need to read from disk)
                elif (previous_id in self.chain_last_cache):
                    new_last_cache[previous_id] = self.chain_last_cache[previous_id]
                    remaining_transactions -= new_last_cache[previous_id].get_block_len()
                else:
                    #read block from disk
                    tmp_block = self.read_block_from_backup(previous_id)
                    #checks block is the same with metadata
                    if not self.check_block_with_metadata(tmp_block, previous_id):
                        return False
                    new_last_cache[previous_id] = tmp_block
                    remaining_transactions -= new_last_cache[previous_id].get_block_len()
            step_back += 1
        self.chain_last_cache = new_last_cache
        #debug
        print("END LAST CACHE SET, id: ", id)
        print(list(self.chain_last_cache.keys()))
        #
        return True

    #load into the cache the block and its neighbours, we assume that the block (id) isn't already in the caches
    def set_random_cache(self, id):
        #debug
        print("START RANDOM CACHE SET, id: ", id)
        #
        remaining_transactions = min(self.RANDOM_CACHE_SIZE, self.n_transactions)
        new_random_cache = {}
        if (remaining_transactions > 0):
            tmp_block = self.read_block_from_backup(id)

            #checks block is the same with metadata
            if not self.check_block_with_metadata(tmp_block, id):
                #debug
                print("AAAAAAAAAA 1")
                #
                return False
            new_random_cache[id] = tmp_block
            remaining_transactions -= new_random_cache[id].get_block_len()

        neighbourhood = 1
        while (remaining_transactions > 0 and (id-neighbourhood > 0 or id + neighbourhood < len(blockchain.chain_metadata) or id+neighbourhood in self.chain_last_cache)):
            previous_id = id-neighbourhood      #block on the left
            next_id = id+neighbourhood          #block on the right

            #check if previous_id is valid
            if (previous_id >= 1 and previous_id < len(blockchain.chain_metadata)):
                #check if previous_block is already stored in random_cache (recycle it, don't need to read from disk)
                if (previous_id in self.chain_random_cache):
                    new_random_cache[previous_id] = self.chain_random_cache[previous_id]
                    remaining_transactions -= new_random_cache[previous_id].get_block_len()
                elif (not(previous_id in self.chain_last_cache)):                        #if previous_block is in last_cache, ignore it
                    #read block from disk
                    tmp_block = self.read_block_from_backup(previous_id)
                    #check block is the same with metadata
                    if not self.check_block_with_metadata(tmp_block, previous_id):
                        #debug
                        print("AAAAAAAAAA 2")
                        #
                        return False
                    new_random_cache[previous_id] = tmp_block
                    remaining_transactions -= new_random_cache[previous_id].get_block_len()

            #check if next_id is valid
            if (next_id >= 1 and next_id < len(blockchain.chain_metadata)):
                #check if next_block is already stored in random_cache (recycle it, don't need to read from disk)
                if (next_id in self.chain_random_cache):
                    new_random_cache[next_id] = self.chain_random_cache[next_id]
                    remaining_transactions -= new_random_cache[next_id].get_block_len()
                elif (not(next_id in self.chain_last_cache)):                        #if next_block is in last_cache, ignore it
                    #read block from disk
                    tmp_block = self.read_block_from_backup(next_id)
                    #check block is the same with metadata
                    if not self.check_block_with_metadata(tmp_block, next_id):
                        #debug
                        print("AAAAAAAAAA 2")
                        #
                        return False
                    new_random_cache[next_id] = tmp_block
                    remaining_transactions -= new_random_cache[next_id].get_block_len()
            neighbourhood += 1
        self.chain_random_cache = new_random_cache
        #debug
        print("END RANDOM CACHE SET, id: ", id)
        print(list(self.chain_random_cache.keys()))
        #
        return True


    def set_random_cache_from(self, id):
        remaining_transactions = min(self.RANDOM_CACHE_SIZE, self.n_transactions)
        new_random_cache = {}
        if ( remaining_transactions > 0):
            tmp_block = self.read_block_from_backup(id)

            #checks block is the same with metadata
            if not self.check_block_with_metadata(tmp_block, id):
                return False
            new_random_cache[id] = tmp_block
            remaining_transactions -= new_random_cache[id].get_block_len()

        #step determine next block that will be added to the cache
        step = 1
        step_direction = 1
        while (remaining_transactions > 0):
            next_id = id+step
            #maybe useless check into the if
            #check if next_id is valid
            #debug
            print("next_id: ", next_id, "remaining_transactions: ", remaining_transactions)
            #
            if (next_id >= 1 and next_id < len(blockchain.chain_metadata)):
                #check if previous_block is already stored in random_cache (recycle it, don't need to read from disk)
                if (next_id in self.chain_random_cache):
                    new_random_cache[next_id] = self.chain_random_cache[next_id]
                    #debug
                    print("THEN, block_id: ", next_id, "; block_sixe: ", new_random_cache[next_id].get_block_len())
                    #
                    remaining_transactions -= new_random_cache[next_id].get_block_len()
                #check if previous_block is already stored in last_cache, if yes, change direction
                elif (next_id in self.chain_last_cache):
                    step = -1
                    step_direction = -1
                    print("ELIF, step: ", step, "; step_direction: ", step_direction)
                else:
                    #read block from disk
                    tmp_block = self.read_block_from_backup(next_id)
                    #checks block is the same with metadata
                    if not self.check_block_with_metadata(tmp_block, next_id):
                        return False
                    new_random_cache[next_id] = tmp_block
                    #debug
                    print("ELSE, block_id: ", next_id,"; block_sixe: ", new_random_cache[next_id].get_block_len())
                    #
                    remaining_transactions -= new_random_cache[next_id].get_block_len()
            #debug
            print("step: ", step, "; step_direction: ", step_direction)
            #
            step += step_direction
        self.chain_random_cache = new_random_cache
        #debug
        print("END RANDOM CACHE SET, id: ", id)
        print(list(self.chain_random_cache.keys()))
        #
        return True


    def get_block_metadata(self, id):
        if id < 0 or id > len(self.chain_metadata):
            return False
        return self.chain_metadata[id]


    def get_block(self, id):

        if id < 0 or id > len(self.chain_metadata):
            return False

        #check if the block is stored in the cache
        if (id in self.chain_last_cache):
            #get the block from the cache
            return self.chain_last_cache[id]

        #check if the block is stored in the cache
        if (id in self.chain_random_cache):
            #get the block from the cache
            #debug
            print("RANDOM CACHED BLOCKS1")
            print(list(self.chain_random_cache.keys()))
            #
            return self.chain_random_cache[id]

        #load the block (and the neighbours) into the random_cache
        if (self.RANDOM_CACHE_SIZE > 0):
            self.set_random_cache(id)
            #debug
            print("RANDOM CACHED BLOCKS2")
            print(list(self.chain_random_cache.keys()))
            #
            return self.chain_random_cache[id]
        else:
            #read block from disk
            tmp_block = self.read_block_from_backup(id)
            #checks block is the same with metadata
            if not self.check_block_with_metadata(tmp_block, id):
                return False
            return tmp_block

    #read a block from file
    def read_block_from_backup(self, id):
        tmp_file = open(backup_path + '/' + str(id), 'r')
        tmp_json = tmp_file.read()
        tmp_dict = json.loads(tmp_json)

        #create transactions objects
        for i in range(0, len(tmp_dict["transactions"])):
            tmp_trans = Transaction(tmp_dict["transactions"][i])
            tmp_dict["transactions"][i] = tmp_trans
        #debug

        #print("TMP_DICT")
        #print(tmp_dict)
        #

        #create block object
        tmp_block = Block(0,0,0,0,0)
        tmp_block.__dict__ = tmp_dict
        return tmp_block


    #read from the backup folder and initialize the chain
    def read_backup(self):
        if(not os.path.isdir(backup_path)):
            return False
        for r, d, f, in os.walk(backup_path):
            backup = f                          #list of the names of the files in the backup folder

        backup = [int(i) for i in backup]
        backup.sort()
        #debug
        #print("SORTED BACKUP")
        #print(type(backup))
        #print(type(backup[0]))
        #print(backup)
        #
        #debug
        #print(backup)
        #
        #build metadata
        for n in backup:
            #parse json from file
            tmp_block = self.read_block_from_backup(n)
            tmp_proof = tmp_block.__dict__["hash"]
            del tmp_block.__dict__["hash"]
            #block validation
            if (not self.is_valid_proof(tmp_block, tmp_proof)):
                return False
            #block metadata
            self.chain_metadata.append({
                "index": tmp_block.index,
                "block_size": tmp_block.get_block_len(),
                "first_transaction": tmp_block.transactions[0].TRANSACTION_ID,
                "last_transaction": tmp_block.transactions[-1].TRANSACTION_ID,
                "hash": tmp_proof,
                "nonce": tmp_block.nonce,
                "previous_hash": tmp_block.previous_hash
            })
            self.n_transactions += tmp_block.get_block_len()

        #initialize last_cache
        self.set_last_cache()
        #initialize random_cache (using greater block_id that is not into the last_cache)
        #check if there are block/transaction out of the last_cache
        if ( len(self.chain_metadata) > len(self.chain_last_cache) ):
            self.set_random_cache( len(self.chain_metadata) - len(self.chain_last_cache) - 1 ) #TODO check correctness
        else:
            self.chain_random_cache = {}

        return True


            #if n == 1:
            #    return

    def get_chain_length(self):
        return len(self.chain_metadata)



app = Flask(__name__)

# the node's copy of blockchain
blockchain = Blockchain()
blockchain.create_genesis_block()
blockchain.read_backup()

# the address to other participating members of the network
peers = set()

# endpoint to submit many new transaction. This will be used by
# our application to add new data (posts) to the blockchain
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    #required_fields = ["author", "content"]

    ''' TODO vedere se serve
     global transaction_fields
    '''

    ''' TODO questo controllo va tolto o affinato
    if not tx_data.get(field):
        return "Invalid transaction data", 404
    '''
    tx_data["timestamp"] = time.time()
    transaction = Transaction(tx_data)
    blockchain.add_new_transaction(transaction)

    return "Success", 201

# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain
@app.route('/new_transaction_multi', methods=['POST']) #tested
def new_transaction_multi():
    tx_data = request.get_json()

    #debug
    print("TX_DATA");
    print(tx_data);

    #required_fields = ["author", "content"]
    #debug
    print("TRANSACTIONS")
    print(len(tx_data))

    ''' TODO vedere se serve
     global transaction_fields
    '''

    for line in tx_data:
        line["timestamp"] = time.time()
        transaction = Transaction(line)
        blockchain.add_new_transaction(transaction)

    mine_unconfirmed_transactions()
    return "Success", 201


        ## TODO test with metadata
# endpoint to return the node's copy of the chain.
# Our application will be using this endpoint to query
# all the posts to display.
@app.route('/chain', methods=['GET'])  #tested
def get_chain():

    chain_data = []
    #debug
    #print("Blockchain SIZE")
    #print(len(blockchain.chain))
    #
    set_random_cache_from(1)
    for block_metadata in blockchain.chain_metadata:

        #controlla che il blocco sia nella cache, in caso contrario setta la cache a partire da quel blocco
        if (not blockchain.check_block_in_cache(block_metadata["index"]) ):
            set_random_cache_from(block_metadata["index"])

        block = blockchain.get_block(block_metadata["index"])
        block_to_add = block.__dict__.copy()

        #debug
        #print("BLOCK BEFORE")
        #print(block_to_add)
        #

        transactions_dict = []
        for i in range(0,len(block_to_add["transactions"])):
            #print("POS")
            #print(i)
            #print(block_to_add["transactions"][i].__dict__)
            transactions_dict.append(block_to_add["transactions"][i].__dict__)
            #block_to_add["transactions"][i] = block_to_add["transactions"][i].__dict__

        block_to_add["transactions"] = transactions_dict

        #debug
        #print("BLOCK AFTER")
        #print(block_to_add)
        #

        chain_data.append(block_to_add)

    #debug
    #print("CHAIN_DATA")
    #print(type(chain_data))
    #print(chain_data)
    #

    return json.dumps({"length": len(chain_data),
                       "chain": chain_data,
                       "peers": list(peers)}, cls=BlockEncoder)


        ## TODO test with metadata
# endpoint to return the transactions of a block gived its id.
# Our application will be using this endpoint to query
# all the posts to display.
@app.route('/blocks/<block_id>', methods=['GET']) #tested
def get_transaction_by_block_id(block_id):

    block = blockchain.get_block(int(block_id))

    if not block:
        return "Block not found", 404

    block_to_add = block.__dict__.copy()

    transactions_dict = []
    for i in range(0,len(block_to_add["transactions"])):

        transactions_dict.append(block_to_add["transactions"][i].__dict__)

    block_to_add["transactions"] = transactions_dict

    return json.dumps({"block": block_to_add}, cls=BlockEncoder)


        ## TODO test with metadata
# endpoint to return the transaction gived its id.
# Our application will be using this endpoint to query
# all the posts to display.
@app.route('/transactions/<transaction_id>', methods=['GET'])
def get_transaction_by_id(transaction_id): #tested
    transaction_id = int(transaction_id)
    print(transaction_id)
    min_id = 1
    max_id = blockchain.get_chain_length() - 1
    med_id = (min_id + max_id) // 2
    med_block_metadata = blockchain.get_block_metadata(med_id)

    #debug
    #print(transaction_id)
    #print("BLOCK ID ", med_id)
    #print("MAX_ID ", max_id)


    while((not ( med_block_metadata["first_transaction"] <= transaction_id <= med_block_metadata["last_transaction"] )
        )
        and min_id != max_id):
        #debug
        #print("MED_BLOCK TRANS_ID ", med_block.transactions[0].TRANSACTION_ID)
        #print("MIN_ID ", min_id)
        #print("MAX_ID ", max_id)
        if(transaction_id < med_block_metadata["first_transaction"]):
            max_id = med_id - 1
        else:
            min_id = med_id + 1
        med_id = (max_id + min_id) // 2
        #print("BLOCK ID ", med_id)
        med_block_metadata = blockchain.get_block_metadata(med_id)

    if(med_block_metadata["first_transaction"] <= transaction_id <= med_block_metadata["last_transaction"]):
        tmp_block = blockchain.get_block(med_block_metadata["index"])
        #return {"transaction" : json.dumps(med_block.get_transaction(transaction_id), cls=TransactionEncoder, sort_keys=True)}
        return json.dumps({"transaction" : tmp_block.get_transaction(transaction_id).__dict__})
    else:
        return "Transaction not found", 404


        ## TODO test with metadata
@app.route('/transactions_pages', methods=['GET'])
def get_transactions_per_pages():
    page = int(request.args.get("page"))
    per_page = int(request.args.get("per_page"))

    print("PAGE ", page)
    print("PER_PAGE ", per_page)

    counter = page*per_page
    i = 1

    if i >= blockchain.get_chain_length():
        return "Page not found", 404

    while counter - blockchain.get_block_metadata(i)["block_size"] >= 0:

        counter -= blockchain.get_block_metadata(i)["block_size"]

        i += 1

        if i >= blockchain.get_chain_length():
            return "Page not found", 404

    block = blockchain.get_block(i).__dict__.copy()

    index = counter
    finished_chain = False

    transactions = []
    j = 0

    while j < per_page and not finished_chain:

        transactions.append(block["transactions"][index].__dict__)

        if index == len(block["transactions"]):
            index = 0
            i += 1

            if i == blockchain.get_chain_length():
                finished_chain = True
            else:
                block = blockchain.get_block(i).__dict__.copy()
        else:
            index += 1

        j += 1

    return json.dumps({"transactions" : transactions})


        ## TODO test with metadata
@app.route('/transactions', methods=['GET']) #tested
def get_flight_status_by_number_and_date():
    op_carrier = request.args.get("OP_CARRIER_FL_NUM")
    date = request.args.get("FL_DATE")
    print("OP_CARRIER ", op_carrier)
    print("FL_DATE", date)

    select_dict = {"OP_CARRIER_FL_NUM" : op_carrier, "FL_DATE" : date}
    result_flights = []

    #initialize cache from the beginning of the chain
    if not blockchain.check_block_in_cache(1):
        blockchain.set_random_cache_from(1)

    for i in range(1, blockchain.get_chain_length()):
        # shift the cache forward
        if (not blockchain.check_block_in_cache(i)):
            blockchain.set_random_cache_from(i)

        block = blockchain.get_block(i)

        for flight in block.transactions:
            result = True
            #print(flight.__dict__.keys())
            if "OP_CARRIER_FL_NUM" not in flight.__dict__.keys():
                print(flight.__dict__)
            else :
                for key in select_dict.keys():

                    if flight.__dict__[key] != select_dict[key]:
                        result = False

                if result:
                    result_flights += [flight.__dict__]


    return json.dumps({"flights" : result_flights})


        ## TODO test with metadata
@app.route('/average_delays', methods=['GET']) #tested
def get_arr_delays_per_dates_and_carrier():
    op_carrier = request.args.get("OP_CARRIER_AIRLINE_ID")
    initial_date = request.args.get('INITIAL_DATE')
    final_date = request.args.get('FINAL_DATE')
    #select_dict = {"OP_CARRIER_FL_NUM" : op_carrier, "FL_DATE" : date}
    filtered_flights_delays = []

    print(initial_date)
    print(final_date)

    #debug
    print("OP_CARRIER ", op_carrier)
    print("INITIAL_DATE ", initial_date)
    print("FINAL_DATE ", final_date)

    #initialize cache from the beginning of the chain
    blockchain.set_random_cache_from(1)
    for i in range(1, blockchain.get_chain_length()):
        # shift the cache forward
        if (not blockchain.check_block_in_cache(i)):
            blockchain.set_random_cache_from(i)
        block = blockchain.get_block(i)

        for flight in block.transactions:
            #print(flight.__dict__["FL_DATE"], ", ", initial_date, ", ", final_date, ", ", flight.__dict__["OP_CARRIER_AIRLINE_ID"])

            if "OP_CARRIER_AIRLINE_ID" not in flight.__dict__.keys():
                print(flight.__dict__)
            else:
                if flight.__dict__["OP_CARRIER_AIRLINE_ID"] == op_carrier and flight.__dict__["FL_DATE"] >= initial_date and flight.__dict__["FL_DATE"] <= final_date:
                    if not flight.__dict__["ARR_DELAY"] == '':
                        #debug
                        #print(flight.__dict__["ARR_DELAY"])
                        filtered_flights_delays += [float(flight.__dict__["ARR_DELAY"])]

    #debug
    #print("FILTERED ", filtered_flights_delays)

    if(len(filtered_flights_delays) > 0):
        return {"average_delay" : sum(filtered_flights_delays)/len(filtered_flights_delays)}
    else:
        return "Not found", 404


        ## TODO test with metadata
@app.route('/flight_counter', methods=['GET']) #tested
def count_flights_from_A_to_B():
    origin = request.args.get("ORIGIN_CITY_NAME")
    destination = request.args.get("DEST_CITY_NAME")
    initial_date = request.args.get('INITIAL_DATE')
    final_date = request.args.get('FINAL_DATE')
    print(initial_date)
    print(final_date)
    print(origin)
    print(destination)

    filtered_flights_counter = 0

    #initialize cache from the beginning of the chain
    blockchain.set_random_cache_from(1)
    for i in range(1, blockchain.get_chain_length()):
        # shift the cache forward
        if (not blockchain.check_block_in_cache(i)):
            blockchain.set_random_cache_from(i)

        block = blockchain.get_block(i)

        for flight in block.transactions:

            if 'ORIGIN_CITY_NAME' not in flight.__dict__.keys():
                print(flight.__dict__)
            else:
                if flight.__dict__['ORIGIN_CITY_NAME'] == origin and flight.__dict__['DEST_CITY_NAME'] == destination and flight.__dict__["FL_DATE"] >= initial_date and flight.__dict__["FL_DATE"] <= final_date:
                    filtered_flights_counter += 1

    return {"filtered_flights_counter" : filtered_flights_counter}



        ## TODO test with metadata
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
        chain_length = blockchain.get_chain_length()
        '''
        consensus()
        if chain_length == blockchain.get_chain_length():
            # announce the recently mined block to the network
            announce_new_block(blockchain.last_block)
        '''
        return "Block #{} is mined.".format(blockchain.last_block_metadata["index"])


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









