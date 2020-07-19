#!/usr/bin/env python3
'''
Flask runner for the Parivahan crawler.

# Usage:

## Dev:
    python3 app.py

## Prod:
    gunicorn3 --bind 0.0.0.0:5000 app:APP
'''

from flask import Flask, request
from lib.crawler import get_reg_details

APP = Flask(__name__)


@APP.route('/')
def get_vehicle_details():
    '''Get vehicle details from registration number.'''
    reg = request.args.get('reg')

    if not reg:
        return 'Usage: http://server/?reg=<vehicle-registration-number>\n', 400

    details = get_reg_details(reg)

    if not details:
        return 'Incorrect response from Parivahan server!\n', 500

    return details


if __name__ == '__main__':
    APP.run(debug=True)
