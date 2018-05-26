# ibm_blockchain

Developing a blockchain application from scratch in Python

Explained in detail [here](https://www.ibm.com/developerworks/cloud/library/cl-develop-blockchain-app-in-python/index.html)

### Instructions to run

Start a blockchain node server,

```sh
>>> python node_server.py
```

Run our application,

```sh
>>> python run_app.py
```

The application should be up and running at [http://localhost:5000](http://localhost:5000).

Here are a few screenshots

1. Posting some content

![image.png](https://github.com/satwikkansal/ibm_blockchain/raw/master/screenshots/1.png)

2. Requesting the node to mine

![image.png](https://github.com/satwikkansal/ibm_blockchain/raw/master/screenshots/2.png)

3. Resyncing with the chain for updated data

![image.png](https://github.com/satwikkansal/ibm_blockchain/raw/master/screenshots/3.png)

To play around by spinning off multiple custom nodes, use the `add_nodes/` endpoint to register a new node. To update the node with which the application syncs, change `CONNECTED_NODE_ADDRESS` field in the [views.py](https://github.com/satwikkansal/ibm_blockchain/blob/master/app/views.py) file.
