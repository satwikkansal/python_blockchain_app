import datetime
import json

import requests
from flask import render_template, redirect, request

from app import app

# The node with which our application interacts, there can be multiple
# such nodes as well.
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

posts = []


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


@app.route('/')
def index():
    fetch_posts()
    return render_template('index2.html',
                           title='YourNet: Decentralized '
                                 'content sharing',
                           posts=posts,
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


def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')
