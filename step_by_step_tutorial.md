
Back in 2008, a whitepaper titled [Bitcoin: A Peer-to-peer electronic cash system](https://bitcoin.org/bitcoin.pdf) was released by an individual (or maybe a group) named Satoshi Nakamoto. It combined cryptographic techniques and peer-to-peer network in a way that there was no need to trust a centralized authority (like banks) to make payments from one person to another person. Bitcoin was born. Apart from Bitcoin, this paper introduced a distributed system of storing data (now popularly known as "blockchain") which had much wider applications than just payments. Since then, there has been a lot of limelight in this field. The blockchain is the underlying technology behind fully-digital cryptocurrencies like Bitcoin and distributed computing technologies like Ethereum.

In this article, we'll be understanding what exactly a blockchain is. And can there be a better way to understand something than actually implementing it? So we'll be implementing a blockchain from scratch and build a simple application that leverages it. We'll be using Python as the programming language since it's an easier language to understand and follow along.

## What is this "Blockchain"?

The blockchain is a certain way of storing data digitally.

The data can literally be anything. For Bitcoin, its the transactions (transfers of Bitcoin from one account to another account), but it can even be files, doesn't matter

The data is stored in the form of blocks which are chained together using hashes. Hence the name "block-chain".

All the magic lies in the way this data is added and stored in the blockchain, which yields some highly desirable characteristics:
- Immutability of history
- Un-hackability of the system
- Persistence of the data
- No single point of failure

How is blockchain able to achieve these characteristics? I'll explain you along the way while we attempt to implement one.

So let's dive right in...

## A bit about our application

To make things more interesting, let's define what the application we're trying to build would do. Our goal is to build a simple website that lets anyone share information/thoughts on it. Since the content will be stored on the blockchain, it is immutable and permanent (ain't no-one can take it down!).

## Implementation

We'll follow a bottom-up approach to implement things. Let's begin with the data that we'd be storing in the blockchain.

### Defining the structure of the data

What is going to be stored in the blockchain? A post on our application will be identified by three essential things:
1. Content
2. Author
3. Timestamp

We'll be storing it in our blockchain in a format that's widely used, JSON. Here's how a post stored in blockchain should look like:

```js
{
    "author": "some_author_name",
    "content": "Some thoughts that author wants to share",
    "timestamp": "The time at which the content was created"
}
```

The generic term "data" is often replaced on the internet by the term "transactions". So just to avoid confusion and maintain consistency, we'll be using the term "transaction" to refer to the post data from now onwards in the post.

### Storing the transactions into blocks

The transactions are packed into blocks. So a block can contain one or many transactions. The blocks containing the transactions are generated frequently and added to the blockchain. Since there can be multiple blocks, each block should have a unique id.

```py
class Block:
    def __init__(self, index, transactions, timestamp):
        self.index = []
        self.transactions = transactions
        self.timestamp = timestamp
```

### Making the blocks immutable

We would like to detect any kind of tampering in the data stored inside the block. In blockchain, this is done using a hash function.

#### What is a hash function?

A hash function is a function that takes data of any size and produces data of a fixed size from it, which generally works to identify the input. Here's an example in Python using sha256 hashing function,

```py
>>> from hashlib import sha256
>>> data = "Some variable length data"
>>> sha256(data).hexdigest()
'b919fbbcae38e2bdaebb6c04ed4098e5c70563d2dc51e085f784c058ff208516'
>>> sha256(data).hexdigest() # no matter how many times you run it, the result is going to be the same 256 character string
'b919fbbcae38e2bdaebb6c04ed4098e5c70563d2dc51e085f784c058ff208516'
```

The characteristics of an ideal hash function are:
- It should be computationally easy to compute.
- Even a single bit change in data should make the hash change altogether.
- It should not be able to guess the input from the output hash.

Now we know what a hash function is. We'll be storing the hash of every block in a field inside our `Block` object to act like a digital fingerprint of data contained in it.

```py
from hashlib import sha256
import json

def compute_hash(block):
     """
    A function that creates the hash of the block.
    """
    block_string = json.dumps(self.__dict__, sort_keys=True)
    return sha256(block_string.encode()).hexdigest()
```

Note: In most cryptocurrencies, even the individual transactions in the block are hashed, to form a hash tree (aka [merkle tree](https://en.wikipedia.org/wiki/Merkle_tree)) and the root of the tree might me used as the hash of the block. It's not a necessary requirement for the functioning of the blockchain, so we're omitting it to keep things neat and simple.

### Chaining the blocks

Okay, now we've set up the blocks. The blockchain is supposed to be a collection of blocks. We can store all the blocks in the python list (the equivalent of an array).

But this is not sufficient, what if someone intentionally replaced a block back in the collection? Creating a new block with altered transactions, computing the hash, and replacing with any older block is no big deal in our current implementation. We would like to maintain the immutability and order of the blocks.

We need a way to make sure that any change in the past blocks invalidates the entire chain. One way to do this is to chain the blocks by the hash. By chaining here, we mean to include the hash of the previous block in the current block. So if the content of any of the previous blocks changes, the hash of the block would change, leading to mismatch with the `previous_hash` field in the next block.

Alright, every block is kind of linked to the previous block by the `previous_hash` field, but what about the very first block? The very first block is called "Genesis block" and is generated manually or by some unique logic in most of the cases. Let's add the `previous_hash` field to the `Block` class and implement the initial structure of our `Blockchain` class.

```py
from hashlib import sha256
import json
import time


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()
```

And here's our `Blockchain` class,

```py
class Blockchain:

    def __init__(self):
        self.unconfirmed_transactions = [] # data yet to get into blockchain
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]
```

#### Proof of Work

There is a problem, if we change the previous block, we can re-compute the hashes of all the following blocks quite easily and create a different valid blockchain. To prevent this, we can make the task of calculating the hash difficult and random.

#### Implementing proof of work

The way we do this is instead of accepting any hash for the block, we add some constraint to it. Let's add a constraint that our hash should start with 2 leading zeroes. Also, we know that unless we change the contents of the block the hash is not going to change.

So we are going to introduce a new field in our block called "nonce". A nonce is a number that we'll keep on changing until we get a hash that satisfies our constraint. The number of leading zeroes (the value `2` in our case) decides the "difficulty" of our Proof Of Work algorithm. Also, you may notice that our Proof Of Work is difficult to compute but easy to verify once we figure out the nonce (to verify, you just have to run the hash function again).

```py
class Blockchain:
    # difficulty of PoW algorithm
    difficulty = 2

    """
    Previous code contd..
    """

    def proof_of_work(self, block):
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
```

Notice that there is no definite logic to figure out the nonce quickly, it's just brute force hit and trial.

#### Adding blocks to the chain

To add a block to the chain, we'll first have to verify if the Proof of Work provided is correct and if the `previous_hash` field of the block to be added points to the hash of latest block in our chain.

Let's see the code for adding blocks into the chain,

```py
class Blockchain:
    """
    Previous code contd..
    """
    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        """
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not self.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    def is_valid_proof(self, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())
```

#### Mining

The transactions don't get away to the blockchain right away. Intially, they are stored in a pool of unconfirmed transactions. The process of putting the unconfirmed transactions in a block and computing Proof Of Work is known as mining of blocks. Once the nonce satisfying our constraints is figured out, we can say that a block has been mined and the block is put into the blockchain.

In most of the cryptocurrencies (including Bitcoin), miners may be awarded some cryptocurrency as a reward for spending their computing power to compute Proof Of Work. Here's how our mining function would look like,

```py
class Blockchain:
    """
    Previous code contd...
    """

    def add_new_transaction(self, transaction):
            self.unconfirmed_transactions.append(transaction)

    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out Proof Of Work.
        """
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        self.unconfirmed_transactions = []
        return new_block.index
```


Alright, we're almost there. The combined code till now is available [here](https://github.com/satwikkansal/ibm_blockchain/blob/3d252de03586ebb96acb689842ca2d451c0eec47/node_server.py).


### Interacting with the network

Okay, now it's time to create interfaces for our node for interaction with other peers as well as the application we're going to build. We'll be using Flask to create a REST-API to interact with our node. Here's the code for it, 

```py
from flask import Flask, request
import requests

app =  Flask(__name__)

# the node's copy of blockchain
blockchain = Blockchain()
```

We need an endpoint for our application to submit a new transaction. This will be used by our application to add new data (posts) to the blockchain

```py
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["author", "content"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invlaid transaction data", 404

    tx_data["timestamp"] = time.time()

    blockchain.add_new_transaction(tx_data)

    return "Success", 201
```


An endpoint to return the node's copy of the chain. Our application will be using this endpoint to query all the posts to display.
```py
@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data})

```

An endpoint to request the node to mine the unconfirmed transactions (if any). We'll be using it to initiate a command to mine from our application itself.
```py
@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    return "Block #{} is mined.".format(result)


# endpoint to query unconfirmed transactions
@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)


app.run(debug=True, port=8000)
```

Now, if you'd like, you can play around with our blockchain by creating some transactions and then mining them using a tool like cURL or Postman.

### Consensus and decentralization

The code that we've implemented till now is meant to run on a single computer. Even though we're linking block with hashes, we still can't trust a single entity. We need multiple nodes to maintain our blockchain. So first, let's create an endpoint to let a node know of other peers in the network.

```py
# the address to other participating members of the network
peers = set()

# endpoint to add new peers to the network.
@app.route('/add_nodes', methods=['POST'])
def register_new_peers():
    nodes = request.get_json()
    if not nodes:
        return "Invalid data", 400
    for node in nodes:
        peers.add(node)

    return "Success", 201
```

You might have realized that there's a problem with multiple nodes. Due to intentional manipulation or unintentional reasons, the copy of chains of few nodes can differ. In that case, we need to agree upon some version of the chain to maintain the integrity of the entire system. We need to achieve consensus.

A simple consensus algorithm could be to agree upon the longest valid chain when the chains of different participants in the network appear to diverge. The rationale behind this approach is the longest chain is a good estimate of the most amount of work done.

```py
def consensus():
    """
    Our simple consensus algorithm. If a longer valid chain is found, our chain is replaced with it.
    """
    global blockchain

    longest_chain = None
    current_len = len(blockchain)

    for node in peers:
        response = requests.get('http://{}/chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True

    return False
```

And now finally, we'd like to develop a way for any node to announce to the network that it has mined a block so that everyone can update their blockchain and move on to mine other transactions. Other nodes can simply verify the proof of work and add it to theie respective chains.

```py
# endpoint to add a block mined by someone else to the node's chain.
@app.route('/add_block', methods=['POST'])
def validate_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"], block_data["transactions"],
                  block_data["timestamp", block_data["previous_hash"]])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


def announce_new_block(block):
    for peer in peers:
        url = "http://{}/add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))
```

The `announce_new_block` method should be called after every block is mined by the node, so that peers can add it to their chains.

### Registering new nodes to the chain

Here's the code for this, the comments are self-explanatory

```py
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
    blockchain = Blockchain()
    for idx, block_data in enumerate(chain_dump):
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"])
        proof = block_data['hash']
        if idx > 0:
            added = blockchain.add_block(block, proof)
            if not added:
                raise Exception("The chain dump is tampered!!")
        else:  # the block is a genesis block, no verification needed
            blockchain.chain.append(block)
    return blockchain
```

### Building our application

Alright, the backend is all set up. The code till now is available [here])(https://github.com/satwikkansal/ibm_blockchain/blob/631346a130a4effc374fc63f58a08de94bae3c8a/node_server.py). Now, it's time to start working on the interface of our application. I've used Jinja2 templating to render the web pages and some CSS to make the page look nice. You can find the entire code [here](https://github.com/satwikkansal/ibm_blockchain), but the main logic lies in the file `Views.py`.

Our application needs to connect to some node in the blockchain network to fetch the data and also to submit new data. There can be multiple such nodes as well.

```py
import datetime
import json

import requests
from flask import render_template, redirect, request

from app import app

.
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

posts = []
```

The `fetch_posts` function gets the data from node's `/chain` endpoint, parses the data and stores it locally.
```py
def fetch_posts():
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)

        global posts
        posts = sorted(content, key=lambda k: k['timestamp'],
                       reverse=True)
```


The application has an HTML form to take user input and then makes a `POST` request to a connected node to add the transaction into the unconfirmed transactions pool. The transaction is then mined by the network and then finally will be fetched once we refresh our website.

```py
@app.route('/submit', methods=['POST'])
def submit_textarea():
    """
    Endpoint to create a new transaction via our application.
    """
    post_content = request.form["content"]
    author = request.form["author"]

    post_object = {
        'author': author,
        'content': post_content,
    }

    # Submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/')
```

## Our application in action!

Yay! It's done. You can find the final code [here](https://github.com/satwikkansal/python_blockchain_app).

### Instructions to run

Start a blockchain node server,

```sh
>>> export FLASK_APP=node_server.py
>>> flask run --port 8000
```

Run our application,

```sh
>>> python run_app.py
```

The application should be up and running at [http://localhost:5000](http://localhost:5000).

Here are a few screenshots

1. Posting some content

[![image.png](https://s18.postimg.cc/ppm7ghuo9/image.png)](https://postimg.org/image/jooijf81x/)

2. Requesting the node to mine

[![image.png](https://s18.postimg.cc/a44vwjqft/image.png)](https://postimg.org/image/mvj23207p/)

3. Resyncing with the chain for updated data

[![image.png](https://s18.postimg.cc/9rdhqdfvt/image.png)](https://postimg.org/image/ed9lyq1et/)

Phew, all done!

You might have noticed a flaw in the application. That anyone can change any name and post any content. While this can also be an intentional feature, this can be bad as well. One way to solve this is creating accounts using [public-private key cryptography](https://en.wikipedia.org/wiki/Public-key_cryptography). Every new user needs a public key (analogous to username) and the private key to be able to post on our application. The keys act as a digital signature. The public key can only decode the content encrypted by the corresponding private key. The transactions will be verified using the public key of the author before adding to any block. This way, we'll know who exactly wrote the message.

## From local machine to the cloud!

We can spin off multiple nodes on the cloud and play around with the app. Alternatively, you can also use a tunneling service like [ngrok](https://ngrok.com/) to create a public URL for your localhost server, and then you'll be able to interact with multiple machines.


## A broader view

What we discussed in this article are the fundamentals of the blockchain, and there are a lot of innovations currently happening in the field. There are different mining algorithms (like Proof Of Stake) and their variations. There are different consensus techniques too. There are permissioned blockchains other than Public blockchains. There are different ways of storing data in the chain. And there are different kind of data that different applications store in the blockchain. There are technologies like ethereum that allow even code to be run in a distributed fashion (aka Smart Contracts). All these innovations form grounds for different Cryptocurrencies and blockchain technologies that you'll see around you. But the fundamentals are more or less the same. So there's a lot for you to explore!
