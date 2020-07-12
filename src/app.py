#!/usr/bin/env python3
'''Flask runner for the Parivahan crawler.'''

from flask import Flask, request
from lib.crawler import get_reg_details

APP = Flask(__name__)


@APP.route('/')
def get_vehicle_details():
    '''Get vehicle details from registration number.'''
    reg = request.args.get('reg')

    if not reg:
        return 'Usage: http://server/?reg=<vehicle-registration-number>\n', 400

    return get_reg_details(reg)


if __name__ == '__main__':
    APP.run(port=8000, threaded=True)
