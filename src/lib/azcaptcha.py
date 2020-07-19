#!/usr/bin/env python3
'''Python 3 interface to the AZcaptcha CAPTCHA-Solver API'''

# The MIT License (MIT)
#
# Copyright (c) 2016 Joel Höner
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Portions © 2020 Ankit Pati
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

from time import sleep
from imghdr import what
from html import unescape
from requests import get, post

BASE_URL = 'https://azcaptcha.com'
REQ_URL = BASE_URL + '/in.php'
RES_URL = BASE_URL + '/res.php'
LOAD_URL = BASE_URL + '/load.php'


class AZCaptchaApi:
    '''Provides an interface to the AZCaptcha API.'''
    def __init__(self, api_key):
        self.api_key = api_key

    def get(self, url, params, **kwargs):
        '''Sends a HTTP GET, for low-level API interaction.'''
        params['key'] = self.api_key
        return get(url, params, **kwargs)

    def post(self, url, data, **kwargs):
        '''Sends a HTTP POST, for low-level API interaction.'''
        data['key'] = self.api_key
        return post(url, data, **kwargs)

    def get_balance(self):
        '''Obtains the balance on our account, in dollars.'''
        return float(self.get(RES_URL, {'action': 'getbalance'}).text)

    def solve(self, file, captcha_parameters=None):
        '''
        Queues a captcha for solving. `file` may either be a path or a file
        object.  Optional parameters for captcha solving may be specified in a
        `dict` via `captcha_parameters`, for valid values see section
        'Additional CAPTCHA parameters' in API documentation here:

        https://azcaptcha.com/
        '''

        # If path was provided, load file.
        if isinstance(file, str):
            with open(file, 'rb') as fin:
                raw_data = fin.read()
        else:
            raw_data = file.read()

        # Detect image format.
        file_ext = what(None, h=raw_data)

        # Send request.
        text = self.post(REQ_URL,
                         captcha_parameters or {
                             'method': 'post',
                         },
                         files={
                             'file': ('captcha.' + file_ext, raw_data),
                         }).text

        # Success?
        if '|' in text:
            captcha_id = text.split('|')[1]
            return _Captcha(self, captcha_id)

        # Nope, failure.
        raise Exception('Operation failed: {}!'.format(text))


class _Captcha:
    '''Represents a captcha that was queued for solving.'''
    def __init__(self, api, captcha_id):
        '''
        Constructs a new captcha awaiting result. Instances should not be
        created manually, but using the `AZCaptchaApi.solve` method.

        :type api: AZCaptchaApi
        '''
        self.api = api
        self.captcha_id = captcha_id
        self._cached_result = None

    def try_get_result(self):
        '''
        Tries to obtain the captcha text. If the result is not yet available,
        `None` is returned.
        '''
        if self._cached_result is not None:
            return self._cached_result

        text = self.api.get(self.api.RES_URL, {
            'action': 'get',
            'id': self.captcha_id,
        }).text

        # Success?
        if '|' in text:
            _, captcha_text = unescape(text).split('|')
            self._cached_result = captcha_text
            return captcha_text

        # Nope, either failure or not ready, yet. Yep, they mistyped 'Captcha'.
        if text in ('CAPCHA_NOT_READY', 'CAPTCHA_NOT_READY'):
            return None

        # Failure.
        raise Exception('Operation failed: {}!'.format(text))

    def await_result(self, sleep_time=1.):
        '''
        Obtains the captcha text in a blocking manner.
        Retries every `sleep_time` seconds.
        '''
        while True:
            result = self.try_get_result()
            if result is not None:
                break
            sleep(sleep_time)
        return result
