#!/usr/bin/env python3
'''Crawler for Parivahan.gov.in website.'''

import sys
from os import getenv
from sys import stderr, argv
from io import BytesIO, SEEK_SET
from requests.sessions import Session
from bs4 import BeautifulSoup
from lib.azcaptcha import AZCaptchaApi

API = AZCaptchaApi(getenv('PARIVAHAN_AZ_CAPTCHA_API_KEY'))
print('CAPTCHA solver balance: ' + str(API.get_balance()), file=stderr)

END_POINTS = {
    'ui': 'https://parivahan.gov.in/rcdlstatus/',
    'api': 'https://parivahan.gov.in/rcdlstatus/vahan/rcDlHome.xhtml',
    'captcha': 'https://parivahan.gov.in/rcdlstatus/DispplayCaptcha',
}


def _get_post_params(soup, img_text, reg1, reg2):
    div = soup.find('div', class_='ui-grid-row bottom-space center-position')
    button_id = div.find('button').get('id').split('j_idt')[1]
    form_id = 'form_rcdl:j_idt{}'.format(button_id)

    table = soup.find('table', class_='vahan-captcha')
    img_id = table.find('img').get('id').split('j_idt')[1].split(':')[0]
    captcha_id = 'form_rcdl:j_idt{}:CaptchaID'.format(img_id)

    # long, fixed parameter
    javax_faces_partial_render = \
        'form_rcdl:pnl_show form_rcdl:pg_show form_rcdl:rcdl_pnl'

    params = {
        'form_rcdl': 'form_rcdl',
        'form_rcdl:tf_reg_no1': reg1,
        'form_rcdl:tf_reg_no2': reg2,
        'javax.faces.partial.ajax': 'true',
        'javax.faces.partial.execute': '@all',
        'javax.faces.partial.render': javax_faces_partial_render,
        'javax.faces.source': form_id,
        captcha_id: img_text,
        form_id: form_id,
    }

    for hidden in soup.find_all('input', {'type': 'hidden'}):
        params[hidden['name']] = \
            hidden['value'] if hidden.has_attr('value') else ''

    return params


def get_reg_details(reg):
    '''Get vehicle details, given a registration number.'''

    with Session() as sess:
        resp = sess.get(END_POINTS['ui'])
        soup = BeautifulSoup(resp.content, 'lxml')
        img_req = sess.get(END_POINTS['captcha'], verify=False)

        with BytesIO() as img_file:
            img_file.write(img_req.content)
            img_file.seek(SEEK_SET)
            captcha = API.solve(img_file)

        img_text = captcha.await_result()

        params = _get_post_params(soup, img_text, reg[:6], reg[6:])

        resp = sess.post(END_POINTS['api'], data=params)

    soup = BeautifulSoup(resp.content, 'lxml')

    table_classes = [
        'table',
        'table-responsive',
        'table-striped',
        'table-condensed',
        'table-bordered',
    ]

    table = soup.find('table', class_=' '.join(table_classes))

    if not table:
        # incorrect response from Parivahan server
        return None

    records = table.find_all('td')

    return {
        records[i].text: records[i + 1].text
        for i in range(0, len(records), 2)
    }


if __name__ == '__main__':
    if argv != 1:
        print('Usage:\n\tcrawler.py <vehicle-registration-number>\n',
              file=stderr)
        sys.exit(1)

    print(get_reg_details(argv[1]))
