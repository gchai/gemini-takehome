# Tested with Python 3.7 and 3.9
# Please use pytest to run.

import jsonschema
import requests
import json
import base64
import hmac
import hashlib
import datetime, time
from jsonschema import validate
import logging
import pytest

base_url = "https://api.sandbox.gemini.com"
endpoint = "/v1/order/new"
url = base_url + endpoint

# Of course in a real environment the keys won't just be sitting around.
gemini_api_key = "account-X12nWyP3H5MwMqpO6yjf"
gemini_api_secret = "9cvGrAbZCgvdZM4mvhpgK7V9nRK".encode()

# Puts a 1 second delay between each test to ensure nonce tokens don't clash.
# This can be alleviated for larger test sets by using multiple accounts
def teardown_function(function):  # the function parameter is optional
    time.sleep(1)


# Reads the JSON Schemas for later use
with open("new_order_schema.json", "r") as file:
    order_status_schema = json.load(file)
with open("error_schema.json", "r") as file:
    error_schema = json.load(file)

# I used JSON Schema validation here to validate the JSON responses. At first I thought I should use RegEx
# but that won't work if the order of the elements come back differently.
# If I had more time, I would tweak the schema so that it's a lot tighter.
# For example, I could make a schema for every error
# And I could have better validations of some of the responses using RegEx
def validate_json(json_data, schema):
    try:
        validate(instance=json_data, schema=schema)
    except jsonschema.exceptions.ValidationError as err:
        print(err)
        err = "Given JSON data is Invalid"
        return False, err

    message = "Given JSON data is Valid"
    return True


# Abstracted this out since it's used a lot
def call_api(payload):
    encoded_payload = json.dumps(payload).encode()
    b64 = base64.b64encode(encoded_payload)
    signature = hmac.new(gemini_api_secret, b64, hashlib.sha384).hexdigest()

    request_headers = {
        "Content-Type": "text/plain",
        "Content-Length": "0",
        "X-GEMINI-APIKEY": gemini_api_key,
        "X-GEMINI-PAYLOAD": b64,
        "X-GEMINI-SIGNATURE": signature,
        "Cache-Control": "no-cache",
    }

    response = requests.post(url, data=None, headers=request_headers)

    return response.json(), response.status_code


# PyTest's parameterize is a great way to run multiple tests while keeping the codebase small and readable.
@pytest.mark.parametrize(
    "test_name, payload_symbol, payload_amount, payload_price, payload_side, payload_type, ",
    [
        ("Basic Test", "btcusd", "5", "3633.00", "buy", "exchange limit"),
        ("Different Symbols", "ethbtc", "5", "3633.00", "buy", "exchange limit"),
        ("Selling Positions", "btcusd", "5", "3633.00", "sell", "exchange limit"),
        ("Higher amount", "btcusd", "1024", "3633.00", "buy", "exchange limit"),
        ("Different Price", "btcusd", "5", "42.00", "buy", "exchange limit"),
        ("Even higher Price", "btcusd", "5", "50000.00", "buy", "exchange limit"),
    ],
)
def test_basic_happypath_tests(
    test_name,
    payload_symbol,
    payload_amount,
    payload_price,
    payload_side,
    payload_type,
):
    print(f"\n====== Test: {test_name} ======")
    t = datetime.datetime.now()
    payload_nonce = str(int(time.mktime(t.timetuple()) * 1000))

    payload = {
        "request": "/v1/order/new",
        "nonce": payload_nonce,
        "symbol": payload_symbol,
        "amount": payload_amount,
        "price": payload_price,
        "side": payload_side,
        "type": payload_type,
    }

    new_order, status_code = call_api(payload)
    print(new_order)

    assert status_code == 200, f"Status code should be 200, its {status_code}"
    assert validate_json(new_order, order_status_schema)


@pytest.mark.parametrize(
    "test_reason, payload_symbol, payload_amount, payload_price, payload_side, payload_type, ",
    {
        ("InvalidPrice", "btcusd", "5", "3633.002", "buy", "exchange limit"),
        (
            "InvalidQuantity",
            "btcusd",
            "lkjad",
            "3633.00",
            "buy",
            "exchange limit",
        ),  # There is a maximum but it's not documented.
        (
            "InvalidQuantity",
            "btcusd",
            "91384652837642836592",
            "3633.00",
            "buy",
            "exchange limit",
        ),
        ("InvalidOrderType", "btcusd", "5", "3633.00", "buy", "not valid type"),
        ("InvalidSide", "btcusd", "5", "3633.00", "hold", "exchange limit"),
        ("InvalidSymbol", "NOSYM", "5", "3633.00", "buy", "exchange limit"),
    },
)
def test_basic_negative_tests(
    test_reason,
    payload_symbol,
    payload_amount,
    payload_price,
    payload_side,
    payload_type,
):
    print(f"\n====== Test: {test_reason} ======")
    t = datetime.datetime.now()
    payload_nonce = str(int(time.mktime(t.timetuple()) * 1000))

    payload = {
        "request": "/v1/order/new",
        "nonce": payload_nonce,
        "symbol": payload_symbol,
        "amount": payload_amount,
        "price": payload_price,
        "side": payload_side,
        "type": payload_type,
    }

    new_order, status_code = call_api(payload)
    print(new_order)

    assert status_code == 400, f"Status code should be 400, its {status_code}"
    assert (
        new_order["reason"] == test_reason
    ), f'Reason should be "{test_reason}", instead its {new_order["reason"]}'
    assert validate_json(new_order, error_schema)


# Tests that the client order ID returns the given ID.
# I used the UNIX timestamp as the ID and I added a string to it so that I can ensure strings are okay.
def test_client_order_id():
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
        "client_order_id": payload_nonce + "buffalo",
    }

    new_order, status_code = call_api(payload)
    print(new_order)

    try:
        assert status_code == 200, f"Status code should be 200, its {status_code}"
        assert (
            new_order["client_order_id"] == payload_nonce + "buffalo"
        ), f'Reason should be "{payload_nonce+"buffalo"}, instead its {new_order["client_order_id"]}'
        assert validate_json(new_order, order_status_schema)
    except AssertionError:
        logging.error("Error in Base Case", exc_info=True)


# Tests the nonce validation by sending two requests with the same nonce
def test_bad_nonce():
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
        assert status_code == 400, f"Status code should be 400, its {status_code}"
        assert (
            new_order["reason"] == "InvalidNonce"
        ), f'Reason should be "InvalidNonce", instead its {new_order["reason"]}'
        assert validate_json(new_order, error_schema)
    except AssertionError:
        logging.error("Error in nonce testing", exc_info=True)
