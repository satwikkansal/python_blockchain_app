import datetime
import json

import requests
from flask import render_template, redirect, request

from app import app

# The node with which our application interacts, there can be multiple
# such nodes as well.
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

page = 0

per_page = 100

posts = []

block_transactions = []

transaction = []

flights_filtered = []

average_delay = "Not available"

flights_counter = "Not available"


def fetch_posts():
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)

    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:

                #tx["index"] = block["index"]
                #tx["hash"] = block["previous_hash"]
                content.append(tx)

        global posts
        posts = sorted(content, key=lambda k: k['timestamp'],
                       reverse=True)

        #remove timestamps
        for post in posts:
            del post["timestamp"]

def fetch_posts_paginated(page, per_page):

    get_chain_address = "{}/transactions_pages".format(CONNECTED_NODE_ADDRESS)
    r = requests.get(get_chain_address, {"page": page, "per_page": per_page})

    global posts

    if(r.status_code == 404):
        posts = []
    else:
        content = json.loads(r.content)["transactions"]

        #posts = sorted(content, key=lambda k: k['timestamp'],reverse=True)

        posts = content

        #print("CONTENT ", posts)

        for post in posts:
            del post["timestamp"]

@app.route('/')
def index():
    #fetch_posts()
    fetch_posts_paginated(page, per_page)
    #debug
    #print("POSTS ", posts)

    #print("BLOCK_TRANSACTIONS ", block_transactions)
    #
    return render_template('index2.html',
                           title='YourNet: Decentralized '
                                 'content sharing',
                           posts=posts,
                           block_transactions = block_transactions,
                           transaction = transaction,
                           page = page,
                           per_page = per_page,
                           flights_filtered = flights_filtered,
                           average_delay = average_delay,
                           flights_counter = flights_counter,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string)


@app.route('/submit', methods=['POST'])
def submit_textarea():
    """
    Endpoint to create a new transaction via our application.
    """
    #TRANSACTION             = request.form["TRANSACTION"]
    YEAR                    = request.form["YEAR"]
    DAY_OF_WEEK             = request.form["DAY_OF_WEEK"]
    FL_DATE                 = request.form["FL_DATE"]
    OP_CARRIER_AIRLINE_ID   = request.form["OP_CARRIER_AIRLINE_ID"]
    OP_CARRIER_FL_NUM       = request.form["OP_CARRIER_FL_NUM"]
    ORIGIN_AIRPORT_ID       = request.form["OP_CARRIER_FL_NUM"]
    ORIGIN                  = request.form["ORIGIN"]
    ORIGIN_CITY_NAME        = request.form["ORIGIN_CITY_NAME"]
    ORIGIN_STATE_NM         = request.form["ORIGIN_STATE_NM"]
    DEST_AIRPORT_ID         = request.form["DEST_AIRPORT_ID"]
    DEST                    = request.form["DEST"]
    DEST_CITY_NAME          = request.form["DEST_CITY_NAME"]
    DEST_STATE_NM           = request.form["DEST_STATE_NM"]
    DEP_TIME                = request.form["DEP_TIME"]
    DEP_DELAY               = request.form["DEP_DELAY"]
    ARR_TIME                = request.form["ARR_TIME"]
    ARR_DELAY               = request.form["ARR_DELAY"]
    CANCELLED               = request.form["CANCELLED"]
    AIR_TIME                = request.form["AIR_TIME"]

    post_object = {
        #'TRANSACTION'           : TRANSACTION,
        'YEAR'                  : YEAR,
        'DAY_OF_WEEK'           : DAY_OF_WEEK,
        'FL_DATE'               : FL_DATE,
        'OP_CARRIER_AIRLINE_ID' : OP_CARRIER_AIRLINE_ID,
        'OP_CARRIER_FL_NUM'     : OP_CARRIER_FL_NUM,
        'ORIGIN_AIRPORT_ID'     : ORIGIN_AIRPORT_ID,
        'ORIGIN'                : ORIGIN,
        'ORIGIN_CITY_NAME'      : ORIGIN_CITY_NAME,
        'ORIGIN_STATE_NM'       : ORIGIN_STATE_NM,
        'DEST_AIRPORT_ID'       : DEST_AIRPORT_ID,
        'DEST'                  : DEST,
        'DEST_CITY_NAME'        : DEST_CITY_NAME,
        'DEST_STATE_NM'         : DEST_STATE_NM,
        'DEP_TIME'              : DEP_TIME,
        'DEP_DELAY'             : DEP_DELAY,
        'ARR_TIME'              : ARR_TIME,
        'ARR_DELAY'             : ARR_DELAY,
        'CANCELLED'             : CANCELLED,
        'AIR_TIME'              : AIR_TIME
    }

    # Submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/')


@app.route('/submit_multi', methods=['POST'])
def submit_textarea_multi():
    """
    Endpoint to create many new transaction via our application.
    """

    new_transactions_json = request.form.getlist("transactions[]");
    new_transactions = [json.loads(line) for line in new_transactions_json]

    # Submit a transaction
    new_tx_address = "{}/new_transaction_multi".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_tx_address,
                  json=new_transactions,
                  headers={'Content-type': 'application/json'})


    return redirect('/')


def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')

@app.route('/blocks', methods=['GET'])
def get_block_from_id():
    block_id = request.args.get("BLOCK_ID")

    block_id_address = "{}/blocks/{}".format(CONNECTED_NODE_ADDRESS, block_id)

    r = requests.get(block_id_address)

    resp = json.loads(r.content)["block"]

    #print(resp)
    content = resp["transactions"]

    print("CONTENT ", content)

    global block_transactions
    block_transactions = sorted(content, key=lambda k: k['timestamp'], reverse=True)

    for transaction in block_transactions:
        del transaction["timestamp"]

    #print("BLOCK_TRANSACTIONS ", block_transactions)

    return redirect('/')

@app.route('/transactions', methods=['GET'])
def get_trans_from_id():

    transaction_id = request.args.get("TRANSACTION_ID")

    transaction_id_address = "{}/transactions/{}".format(CONNECTED_NODE_ADDRESS, transaction_id)

    r = requests.get(transaction_id_address)

    #print("RESP CONTENT", json.loads(r.content)["transaction"])

    global transaction

    transaction += [json.loads(r.content)["transaction"]]

    #print("TRANSACTION ", transaction)

    #print(resp)

    return redirect('/')


@app.route('/filter_transactions', methods=['GET'])
def get_trans_from_filters():

    transaction_id_address = "{}/transactions".format(CONNECTED_NODE_ADDRESS)

    r = requests.get(transaction_id_address, params={"OP_CARRIER_FL_NUM": request.args.get("OP_CARRIER_FL_NUM"), "FL_DATE": request.args.get("FL_DATE")})

    print("RESP ", r.content)
    print("RESP CONTENT", json.loads(r.content)["flights"])

    global flights_filtered

    flights_filtered = json.loads(r.content)["flights"]

    print("flights_filtered ", flights_filtered)

    #print(resp)

    return redirect('/')

@app.route('/average_delays', methods=['GET'])
def average_delay_of_flight():

    average_delay_address = "{}/average_delays".format(CONNECTED_NODE_ADDRESS)

    r = requests.get(average_delay_address, params={"OP_CARRIER_AIRLINE_ID": request.args.get("OP_CARRIER_AIRLINE_ID"), 'INITIAL_DATE': request.args.get('INITIAL_DATE'), 'FINAL_DATE': request.args.get('FINAL_DATE')})

    #debug
    print("RESP ", r.content)


    global average_delay

    #debug
    print(r.status_code)

    if r.status_code != 404:

        #debug
        print("RESP CONTENT", json.loads(r.content)["average_delay"])

        average_delay = json.loads(r.content)["average_delay"]

        #debug
        print("average_delay ", average_delay)

    else:
        average_delay = "Not available"
    #print(resp)

    return redirect('/')


@app.route('/flight_counter', methods=['GET'])
def count_flights_from_A_to_B():

    flights_counter_address = "{}/flight_counter".format(CONNECTED_NODE_ADDRESS)

    r = requests.get(flights_counter_address, params={"ORIGIN_CITY_NAME": request.args.get("ORIGIN_CITY_NAME"), "DEST_CITY_NAME": request.args.get("DEST_CITY_NAME"), 'INITIAL_DATE': request.args.get('INITIAL_DATE'), 'FINAL_DATE': request.args.get('FINAL_DATE')})

    #debug
    print("RESP ", r.content)

    global flights_counter

    #debug
    print(r.status_code)

    if r.status_code != 404:

        #debug
        print("RESP CONTENT", json.loads(r.content)["filtered_flights_counter"])

        flights_counter = json.loads(r.content)["filtered_flights_counter"]

        #debug
        print("flights_counter ", flights_counter)

    else:
        flights_counter = "Not available"
    #print(resp)

    return redirect('/')

@app.route('/transactions_paginated', methods=['GET'])
def get_transactions_per_page():

    global page
    #global per_page

    #page = request.args.get("page")
    #per_page = request.args.get("per_page")

    direction = request.args.get("direction")


    if direction == "next" :
        page += 1
    else:
        if(page != 0):
            page -= 1

    print("ciao ", page)

    return redirect('/')

    