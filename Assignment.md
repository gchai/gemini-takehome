Overview: Frontend Takehome 

Gemini supports Institutional customers as well as Retail clients. If institutions are interested in our program, we encourage them to fill out the following form and submit it, so that we may contact them.

Your task is to generate some test automation using Selenium and Python that will test not only the typical usage of the form, but negative test cases also.

    Be able to quantify the number of discrete test cases

    Your code should be scalable and easy to maintain

    Include both ‘Happy Path’ and negative tests and be able to distinguish both

    Be prepared to talk through your coding choices, your style and your logic

Goal:

Automate the Institutional Client Registration form in Gemini’s sandbox environment.

    Start at exchange.sandbox.gemini.com

    Click ‘Create new account’ link

    Click ‘Create a business account’ link

    You should now be on: https://exchange.sandbox.gemini.com/register/institution

    Perform happy path and negative testing, demonstrating that the form works with good test data, and prevents users from entering bad data.

These tests should be crafted in a way that allows Developers, other QA Engineers and even Business Analysts an opportunity to read the tests and understand the intent of them, but no BDD or other tools should be used. Please create your solution using strictly Python and Selenium. Python packages may be included, in that case please detail what should be installed and the method you used to install the packages.

 

Note: 

You may complete the coding challenge is the language of your choosing.  However Python would be preferred.  
 _______________________________________________________________________________

Backend Take home - Background:

Gemini is a digital asset exchange. Customers can buy and sell dozens of different cryptocurrencies 
and tokens for various fiat currencies. For sophisticated customers, Gemini provides a REST API so 
that customers can place those orders programmatically.

 

The Problem:

The new order API endpoint is described here.
https://docs.gemini.com/rest-api/#new-order
How will you test it?

 

The Solution:

- Please code up a suite of functional test cases in the language of your choice
- Include both positive and negative cases
- Be able to quantify the number of distinct tests run
- You may consume other API endpoints to aid in your testing, but do not attempt
   to test any other API endpoints (e.g., order status). The objective here is to rigorously 
  test this one endpoint as thoroughly as you can.
- Clearly articulate your assumption

 

Sandbox credentials: 

URL: https://api.sandbox.gemini.com

 

Key:account-X12nWyP3H5MwMqpO6yjf

Secret:9cvGrAbZCgvdZM4mvhpgK7V9nRK

Please submit here:
https://app.greenhouse.io/tests/3e27e53d93e4f3c0d816d16020b1b925?utm_medium=email&utm_source=TakeHomeTest