import jsonschema
import requests
import json
import base64
import hmac
import hashlib
import datetime, time
from jsonschema import validate
import logging

base_url = "https://api.sandbox.gemini.com"
endpoint = "/v1/order/new"
url = base_url + endpoint

gemini_api_key = "account-X12nWyP3H5MwMqpO6yjf"
gemini_api_secret = "9cvGrAbZCgvdZM4mvhpgK7V9nRK".encode()

# Reads the JSON Schemas for later use
with open('new_order_schema.json', 'r') as file:
    order_status_schema = json.load(file)
with open('error_schema.json', 'r') as file:
    error_schema = json.load(file)

def validate_json(json_data, schema):
    try:
        validate(instance=json_data, schema=schema)
    except jsonschema.exceptions.ValidationError as err:
        print(err)
        err = "Given JSON data is InValid"
        return False, err

    message = "Given JSON data is Valid"
    return True

def call_api(payload):
    encoded_payload = json.dumps(payload).encode()
    b64 = base64.b64encode(encoded_payload)
    signature = hmac.new(gemini_api_secret, b64, hashlib.sha384).hexdigest()

    request_headers = {'Content-Type': "text/plain",
                       'Content-Length': "0",
                       'X-GEMINI-APIKEY': gemini_api_key,
                       'X-GEMINI-PAYLOAD': b64,
                       'X-GEMINI-SIGNATURE': signature,
                       'Cache-Control': "no-cache"}

    response = requests.post(url,
                             data=None,
                             headers=request_headers)

    return response.json(), response.status_code

# Smoke test
# Given the base case given by the documentation, this should have a response
def base_case():
    t = datetime.datetime.now()
    payload_nonce = str(int(time.mktime(t.timetuple()) * 1000))

    payload = {
        "request": "/v1/order/new",
        "nonce": payload_nonce,
        "symbol": "btcusd",
        "amount": "5",
        "price": "3633.00",
        "side": "buy",
        "type": "exchange limit",
    }

    new_order, status_code = call_api(payload)
    print(new_order)

    try:
        assert status_code == 200, f'Status code should be 200, its {status_code}'
        assert validate_json(new_order, order_status_schema)
    except AssertionError:
        logging.error("Error in Base Case", exc_info=True)

# Tests that the client order ID returns the given ID. I used the UNIX timestamp as the ID and I added a string to it so that I can ensure it's a string.
def client_order_id():
    t = datetime.datetime.now()
    payload_nonce = str(int(time.mktime(t.timetuple()) * 1000))

    payload = {
        "request": "/v1/order/new",
        "nonce": payload_nonce,
        "symbol": "btcusd",
        "amount": "5",
        "price": "3633.00",
        "side": "buy",
        "type": "exchange limit",
        "client_order_id": payload_nonce+"buffalo"
    }

    new_order, status_code = call_api(payload)
    print(new_order)

    try:
        assert status_code == 200, f'Status code should be 200, its {status_code}'
        assert new_order["client_order_id"] == payload_nonce+"buffalo", f'Reason should be "{payload_nonce+"buffalo"}, instead its {new_order["client_order_id"]}'
        assert validate_json(new_order, order_status_schema)
    except AssertionError:
        logging.error("Error in Base Case", exc_info=True)


def negative_case_bad_price():
    t = datetime.datetime.now()
    payload_nonce = str(int(time.mktime(t.timetuple()) * 1000))

    payload = {
        "request": "/v1/order/new",
        "nonce": payload_nonce,
        "symbol": "btcusd",
        "amount": "5",
        "price": "3633.002",
        "side": "buy",
        "type": "exchange limit",
    }

    new_order, status_code = call_api(payload)
    print(new_order)

    try:
        assert status_code == 400, f'Status code should be 400, its {status_code}'
        assert new_order["reason"] == "InvalidPrice", f'Reason should be "InvalidPrice", instead its {new_order["reason"]}'
        assert validate_json(new_order, error_schema)
    except AssertionError:
        logging.error("Error in Base Case", exc_info=True)

def negative_case_bad_amount():
    t = datetime.datetime.now()
    payload_nonce = str(int(time.mktime(t.timetuple()) * 1000))

    payload = {
        "request": "/v1/order/new",
        "nonce": payload_nonce,
        "symbol": "btcusd",
        "amount": "12123145125451233.15123123",
        "price": "3633.00",
        "side": "buy",
        "type": "exchange limit",
    }

    new_order, status_code = call_api(payload)
    print(new_order)

    try:
        assert status_code == 400, f'Status code should be 400, its {status_code}'
        assert new_order["reason"] == "InvalidQuantity", f'Reason should be "InvalidQuantity", instead its {new_order["reason"]}'
        assert validate_json(new_order, error_schema)
    except AssertionError:
        logging.error("Error in Base Case", exc_info=True)

def negative_case_bad_nonce():
    t = datetime.datetime.now()
    payload_nonce = str(int(time.mktime(t.timetuple()) * 1000))

    payload = {
        "request": "/v1/order/new",
        "nonce": payload_nonce,
        "symbol": "btcusd",
        "amount": "5",
        "price": "3633.00",
        "side": "buy",
        "type": "exchange limit",
    }

    call_api(payload)
    new_order, status_code = call_api(payload)
    print(new_order)

    try:
        assert status_code == 400, f'Status code should be 400, its {status_code}'
        assert new_order["reason"] == "InvalidNonce", f'Reason should be "InvalidNonce", instead its {new_order["reason"]}'
        assert validate_json(new_order, error_schema)
    except AssertionError:
        logging.error("Error in nonce testing", exc_info=True)

def run_all_test_cases():
    base_case()
    negative_case_bad_amount()