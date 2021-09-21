# Gabe Chai's Gemini QA API Takehome Assignment

## Tests
There are currently 32 tests

Some tests are currently failing

* There's some edge case issues where BTCUSD does not work.
  * Stop limit for BTCUSD works only intermittently. I have reported this to the recruiter.
* Indication of Interest fails no matter what you throw at it, it seems to be deprecated but the API documentation still shows it
* Auction fails if its outside of auction hours. A possible workaround could be to either:
  * Change the expectation with the current time
  * only run the test during auction hours.

## How to run
This has been tested on Python 3.7 and 3.9, on Windows as well as macOS.
To run the tests, please `cd` to the directory and run `pytest`m
