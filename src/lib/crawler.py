#!/usr/bin/env python3
'''Crawler for Parivahan.gov.in website.'''

from os import getenv
from sys import stderr, argv
import sys
import requests
from bs4 import BeautifulSoup
from azcaptchaapi import AZCaptchaApi

API = AZCaptchaApi(getenv('PARIVAHAN_AZ_CAPTCHA_API_KEY'))
print('CAPTCHA solver balance: ' + API.get_balance(), file=stderr)


def get_reg_details(reg):
    '''Get vehicle details, given a registration number.'''

    end_points = {
        'ui': 'https://parivahan.gov.in/rcdlstatus/',
        'api': 'https://parivahan.gov.in/rcdlstatus/vahan/rcDlHome.xhtml',
        'captcha': 'https://parivahan.gov.in/rcdlstatus/DispplayCaptcha',
    }

    sess = requests.session()
    resp = sess.get(end_points['ui'])
    soup = BeautifulSoup(resp.content, 'lxml')
    img_req = sess.get(end_points['captcha'], verify=False)

    with open('img.png', 'wb') as img_file:
        img_file.write(img_req.content)

    with open('img.png', 'rb') as captcha_file:
        captcha = API.solve(captcha_file)

    img_text = captcha.await_result()

    params = {
        'javax.faces.partial.ajax': 'true',
        'javax.faces.source': 'form_rcdl:j_idt43',
        'javax.faces.partial.execute': '@all',
        'javax.faces.partial.render':
        'form_rcdl:pnl_show form_rcdl:pg_show form_rcdl:rcdl_pnl',
        'form_rcdl:j_idt43': 'form_rcdl:j_idt43',
        'form_rcdl': 'form_rcdl',
        'form_rcdl:tf_reg_no1': reg[:5],
        'form_rcdl:tf_reg_no2': reg[5:],
        'form_rcdl:j_idt32:CaptchaID': img_text,
    }

    for hidden in soup.find_all('input', {'type': 'hidden'}):
        params[hidden['name']] = \
            hidden['value'] if hidden.has_attr('value') else ''

    resp = sess.post(end_points['api'], data=params)
    soup = BeautifulSoup(resp.content, 'lxml')

    table_classes = [
        'table',
        'table-responsive',
        'table-striped',
        'table-condensed',
        'table-bordered',
    ]

    table = soup.find('table', class_=' '.join(table_classes))
    records = table.find_all('td')

    return {
        records[i].text: records[i + 1].text
        for i in range(len(records), 2)
    }


if __name__ == '__main__':
    if argv != 1:
        print('Usage:\n\tcrawler.py <vehicle-registration-number>\n',
              file=stderr)
        sys.exit(1)

    print(get_reg_details(argv[1]))
