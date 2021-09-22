# Tested with Python 3.7 and 3.9
# Please use pytest to run.

# There are currently 34 tests
# Some tests are currently failing
# There's some edge case issues where BTCUSD does not work. (Stop limit for BTCUSD didn't work earlier, but it works now
# Indication of Interest fails no matter what you throw at it, it seems to be deprecated but the API documentation still shows it
# Auction fails if its outside of auction hours. I noted a workaround below
#     either change the expectation with the current time, or only run the test during auction hours.
#     Depends on business needs


import jsonschema
import requests
import json
import base64
import hmac
import hashlib
import datetime, time
from jsonschema import validate
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
# Assumes that the schema is up to date and will not change.
# Currently the API documentation does not make it easy to make Schemas so I had to make this manually
# I would suggest using Swagger for API Documentation
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
# This also assumes that the authentication works
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
    "test_name, payload_symbol, payload_amount, payload_price, payload_side, payload_type",
    [
        ("Basic Test", "btcusd", "5", "3633.00", "buy", "exchange limit"),
        ("Different Symbols", "ethbtc", "5", "3633.00", "buy", "exchange limit"),
        ("Selling Positions", "btcusd", "5", "3633.00", "sell", "exchange limit"),
        ("Higher amount", "btcusd", "1024", "3633.00", "buy", "exchange limit"),
        ("Different Price", "btcusd", "5", "42.00", "buy", "exchange limit"),
        ("Even higher Price", "btcusd", "5", "50000.00", "buy", "exchange limit"),
        (
            "Testing lower limit of ETH",
            "ethbtc",
            "0.001",
            "1000",
            "buy",
            "exchange limit",
        ),
        (
            "Testing lower limit of BTC",
            "btceur",
            "0.00001",
            "1000",
            "buy",
            "exchange limit",
        ),
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
    assert (
        new_order["symbol"] == payload_symbol
    ), f'Symbol should be "{payload_symbol}", instead its {new_order["symbol"]}'
    assert (
        new_order["exchange"] == "gemini"
    ), f'Exchange should be "gemini", instead its {new_order["exchange"]}'
    assert (
        new_order["side"] == payload_side
    ), f'Side should be "{payload_side}", instead its {new_order["side"]}'
    assert (
        new_order["type"] == payload_type
    ), f'Order Type should be "{payload_type}", instead its {new_order["type"]}'
    assert float(new_order["original_amount"]) == float(
        payload_amount
    ), f'Amount should be "{payload_amount}", instead its {new_order["original_amount"]}'
    assert float(new_order["price"]) == float(
        payload_price
    ), f'Price should be "{payload_price}", instead its {new_order["price"]}'


# I could have combined the negative and the happy path basic tests, but I like having the visual separation.
@pytest.mark.parametrize(
    "test_reason, payload_symbol, payload_amount, payload_price, payload_side, payload_type",
    {
        (
            "InvalidPrice",
            "btcusd",
            "5",
            "3633.002",
            "buy",
            "exchange limit",
        ),  # >2 decimals for price
        (
            "InvalidPrice",
            "btcusd",
            "5",
            "-3633.00",
            "buy",
            "exchange limit",
        ),  # negatice price
        (
            "InvalidPrice",
            "btcusd",
            "5",
            "notint",
            "buy",
            "exchange limit",
        ),  # Not a float price
        (
            "InvalidQuantity",
            "btcusd",
            "lkjad",
            "3633.00",
            "buy",
            "exchange limit",
        ),
        (
            "InvalidQuantity",
            "btcusd",
            "91384652837642836592",
            "3633.00",
            "buy",
            "exchange limit",
        ),  # There is a maximum but it's not documented.
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


# Tests the stop limits and the variables it has
@pytest.mark.parametrize(
    "test_name, payload_symbol, payload_amount, payload_price, payload_side, payload_type, payload_stop_price, schema, resp_code",
    [
        # For some reason, BTC Stop limit BUY was bugged when I initially tested it,
        # it will always return "Invalid price for symbol BTCUSD: 43633.00" for whatever reason
        # I have tried to set it to different numbers, but it doesn't work. Other currencies and BTCUSD SELL work.
        # Note from later, this works now
        (
            "BTC Stop Limit",
            "btcusd",
            "5",
            "43633.15",
            "buy",
            "exchange stop limit",
            "43600.00",
            order_status_schema,
            200,
        ),
        (
            "BTCUSD Sell Stop Limit",
            "btcusd",
            "5",
            "5000.00",
            "sell",
            "exchange stop limit",
            "5001.00",
            order_status_schema,
            200,
        ),
        (
            "ETHBTC Sell Stop Limit",
            "btcusd",
            "5",
            "5000.00",
            "sell",
            "exchange stop limit",
            "5001.00",
            order_status_schema,
            200,
        ),
        (
            "ETHBTC Buy Stop Limit",
            "ethbtc",
            "5",
            "5000.00",
            "buy",
            "exchange stop limit",
            "4999.00",
            order_status_schema,
            200,
        ),
        (
            "ETHBTC Buy Stop Limit Float",
            "ethbtc",
            ".1",
            "2000.00",
            "buy",
            "exchange stop limit",
            "1900.00",
            order_status_schema,
            200,
        ),
        (
            "ETHBTC Buy Stop Limit Negative",
            "ethbtc",
            "5",
            "5000.00",
            "buy",
            "exchange stop limit",
            "5001.00",
            error_schema,
            400,
        ),
        (
            "BTCUSD Sell Stop Limit Negative",
            "btcusd",
            "5",
            "5000.00",
            "sell",
            "exchange stop limit",
            "4999.00",
            error_schema,
            400,
        ),
        (
            "ETHBTC Sell Stop Limit too high",
            "btcusd",
            "5",
            "5000.00",
            "sell",
            "exchange stop limit",
            "50000.00",
            error_schema,
            400,
        ),
    ],
)
def test_stop_limit(
    test_name,
    payload_symbol,
    payload_amount,
    payload_price,
    payload_side,
    payload_type,
    payload_stop_price,
    schema,
    resp_code,
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
        "stop_price": payload_stop_price,
    }

    new_order, status_code = call_api(payload)
    print(new_order)

    assert (
        status_code == resp_code
    ), f"Status code should be {resp_code}, its {status_code}"
    assert validate_json(new_order, schema)
    if resp_code == 200:
        assert (
            new_order["symbol"] == payload_symbol
        ), f'Symbol should be "{payload_symbol}", instead its {new_order["symbol"]}'
        assert (
            new_order["exchange"] == "gemini"
        ), f'Exchange should be "gemini", instead its {new_order["exchange"]}'
        assert (
            new_order["side"] == payload_side
        ), f'Side should be "{payload_side}", instead its {new_order["side"]}'
        assert (
            new_order["type"] == "stop-limit"
        ), f'Order Type should be "stop-limit", instead its {new_order["type"]}'
        assert float(new_order["original_amount"]) == float(
            payload_amount
        ), f'Amount should be "{payload_amount}", instead its {new_order["original_amount"]}'
        assert float(new_order["price"]) == float(
            payload_price
        ), f'Price should be "{payload_price}", instead its {new_order["price"]}'
        assert float(new_order["stop_price"]) == float(
            payload_stop_price
        ), f'Stop price should be "{payload_stop_price}", instead it is {new_order["stop_price"]}'


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

    assert status_code == 200, f"Status code should be 200, its {status_code}"
    assert (
        new_order["client_order_id"] == payload_nonce + "buffalo"
    ), f'Reason should be "{payload_nonce+"buffalo"}, instead its {new_order["client_order_id"]}'
    assert validate_json(new_order, order_status_schema)


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

    assert status_code == 400, f"Status code should be 400, its {status_code}"
    assert (
        new_order["reason"] == "InvalidNonce"
    ), f'Reason should be "InvalidNonce", instead its {new_order["reason"]}'
    assert validate_json(new_order, error_schema)


# Tests the order options
@pytest.mark.parametrize(
    "test_name, payload_symbol, payload_amount, payload_price, payload_side, payload_type, payload_options, resp_code",
    [
        (
            "Maker or Cancel Test",
            "btcusd",
            "5",
            "3633.00",
            "buy",
            "exchange limit",
            ["maker-or-cancel"],
            200,
        ),
        (
            "Immediate or Cancel Test",
            "btcusd",
            "5",
            "3633.00",
            "buy",
            "exchange limit",
            ["immediate-or-cancel"],
            200,
        ),
        (
            "Fill or Kill",
            "btcusd",
            "5",
            "3633.00",
            "buy",
            "exchange limit",
            ["fill-or-kill"],
            200,
        ),
        # Auction tests can only run on certain times of the day.
        # Couple ways we can handle this.
        # Only run it during the hours that it's expected to run?
        # Program in a function that checks the time and
        #     if it's outside of normal hours we can expect a 400, otherwise a 200.
        (
            "Auction Test",
            "btcusd",
            "5",
            "3633.00",
            "buy",
            "exchange limit",
            ["auction-only"],
            200,
        ),
        # Indication of interest runs into the same issue as before where btcusd has some bug that causes an invalid price error.
        # Interestingly, the API response to multiple options seems to infer that "Indication if Interest" is no longer supported
        # it states: A single order supports at most one of these options: ['maker-or-cancel', 'immediate-or-cancel', 'auction-only', 'fill-or-kill']
        (
            "Indication of Interest Test",
            "ethbtc",
            "5",
            "1000.00",
            "sell",
            "exchange limit",
            ["indication-of-interest"],
            200,
        ),
        (
            "Multiple Option Test",
            "btcusd",
            "5",
            "3633.00",
            "buy",
            "exchange limit",
            ["maker-or-cancel", "immediate-or-cancel"],
            400,
        ),
    ],
)
def test_order_options(
    test_name,
    payload_symbol,
    payload_amount,
    payload_price,
    payload_side,
    payload_type,
    payload_options,
    resp_code,
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
        "options": payload_options,
    }

    new_order, status_code = call_api(payload)
    print(new_order)

    assert (
        status_code == resp_code
    ), f"Status code should be {resp_code}, its {status_code}"
    assert validate_json(new_order, order_status_schema)

    if resp_code == 200:
        assert (
            new_order["symbol"] == payload_symbol
        ), f'Symbol should be "{payload_symbol}", instead its {new_order["symbol"]}'
        assert (
            new_order["exchange"] == "gemini"
        ), f'Exchange should be "gemini", instead its {new_order["exchange"]}'
        assert (
            new_order["side"] == payload_side
        ), f'Side should be "{payload_side}", instead its {new_order["side"]}'
        assert (
            new_order["type"] == payload_type
        ), f'Order Type should be "{payload_type}", instead its {new_order["type"]}'
        assert float(new_order["original_amount"]) == float(
            payload_amount
        ), f'Amount should be "{payload_amount}", instead its {new_order["original_amount"]}'
        assert float(new_order["price"]) == float(
            payload_price
        ), f'Price should be "{payload_price}", instead its {new_order["price"]}'
        assert (
            new_order["options"] == payload_options
        ), f'Order option should be {payload_options}, instead its {new_order["options"]}'
