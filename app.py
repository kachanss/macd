from flask import Flask, request, jsonify
from flask_jsonpify import jsonpify
from flask_socketio import SocketIO, send, emit
import requests
import time
import stockstats
from threading import Lock

from .utils import fetch, get_macd_by_id
from .macd import MACD

macd_objects = []

app = Flask(__name__)
app.debug = True


@app.route('/macd', methods=['GET'])
def get_all_macd_objects():
    """
    Return all MACD-objects

    :return: list of dict
    """

    global macd_objects

    return jsonpify(macd_objects)


@app.route('/addplato', methods=['PUT'])
def addplato():
    """
    Create the new MACD-object and store it in 'macd_objects' list globally

    :query_param pair
    :query_param fast_period
    :query_param slow_period
    :query_param signal_period    
    :query_param time_period
    :query_param plato_ids

    :return: dict
    """

    params = request.args

    if MACD.paramsIsValid(params):
        return 'Error'
    
    global macd_objects  

    # request to Plato-microservice
    macd = MACD(params['pair'], params['fast_period'], params['slow_period'], params['signal_period'], params['time_period'], params['plato_ids'])
  
    try:
        sdf = fetch(macd.pair, macd.time_period)
    except:
        return jsonpify({ 'message': 'Error occured by fetching data from Plato-microservice', 'status': 1 })

    sdf = macd.calculate_coefficient(sdf)
    
    macd_objects.append(macd.__dict__)

    print(macd_objects)
    return jsonpify(macd.__dict__)


@app.route('/calc/<string:plato_ids>', methods=['PUT'])
def calc(plato_ids):
    """
    Calculate the new macd-coefficients for existing MACD-object by 'plato_ids'

    :param plato_id: Id of MACD-object
    :return: dict
    """
    
    global macd_objects

    macd = get_macd_by_id(plato_ids, macd_objects)

    # check if return empty
    if macd == None:
        return jsonpify({ 'message': 'Object is not exists', 'status': 1 })
    else:
        macd_objects.remove(macd)
        macd = MACD(macd['pair'], macd['fast_period'], macd['slow_period'], macd['signal_period'], macd['time_period'], macd['plato_ids'])
        

    try:
        sdf = fetch(macd.pair, macd.time_period)
    except:
        return jsonpify({ 'message': 'Error occured by fetching data from Plato-microservice', 'status': 1 })

    sdf = macd.calculate_coefficient(sdf)

    macd_objects.append(macd.__dict__)

    print(macd_objects)
    return jsonpify(macd.__dict__)


@app.route('/delete/macd/<string:plato_ids>', methods=['DELETE'])
def delete_macd_object(plato_ids):
    """
    Delete the MACD-object by 'plato_ids'

    :param plato_id: Id of MACD-object

    :return: None or dict
    """
    global macd_objects

    item = get_macd_by_id(plato_ids, macd_objects)

    if item != None:
        macd_objects.remove(item)
    else:
        return jsonpify({ 'message': 'Object is not exists', 'status': 1 })

    return jsonpify({ 'message': 'Object has been deleted', 'status': 0 })



if __name__ == '__main__':
    app.run() # Run app