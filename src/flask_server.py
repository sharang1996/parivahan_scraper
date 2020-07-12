import os
import requests
from azcaptchaapi import AZCaptchaApi
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

app = Flask(__name__)

key = os.getenv("api_key")
api = AZCaptchaApi(key)

def get_reg_details(reg1, reg2):
    sess = requests.session()

    resp = sess.get('https://parivahan.gov.in/rcdlstatus/')

    soup = BeautifulSoup(resp.content, 'lxml')

    img_req = sess.get('https://parivahan.gov.in/rcdlstatus/DispplayCaptcha', verify=False)

    with open('img.png', 'wb')as f:
        f.write(img_req.content)

    with open('img.png', 'rb') as captcha_file:
        captcha = api.solve(captcha_file)

    img_text = captcha.await_result()

    data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'form_rcdl:j_idt43',
            'javax.faces.partial.execute': '@all',
            'javax.faces.partial.render': 'form_rcdl:pnl_show form_rcdl:pg_show form_rcdl:rcdl_pnl',
            'form_rcdl:j_idt43': 'form_rcdl:j_idt43',
            'form_rcdl': 'form_rcdl',
            'form_rcdl:tf_reg_no1': reg1,
            'form_rcdl:tf_reg_no2': reg2,
            'form_rcdl:j_idt32:CaptchaID': img_text,
    }

    hidden_inputs = soup.find_all("input", {"type": "hidden"})
    if len(hidden_inputs) > 0:
        for hidden in hidden_inputs:
            if hidden.has_attr('value'):
                data[hidden['name']] = hidden['value']
            else:
                data[hidden['name']] = ''

    resp = sess.post('https://parivahan.gov.in/rcdlstatus/vahan/rcDlHome.xhtml', data = data)
    soup = BeautifulSoup(resp.content, 'lxml')

    table = soup.find('table', class_='table table-responsive table-striped table-condensed table-bordered')
    tds = table.find_all('td')

    d = {}

    for i in range(0,len(tds),2):
        key = tds[i].text
        value = tds[i+1].text
        d[key] = value

    return d

@app.route('/regdetails')
def get_status():
    reg_1 = request.args.get('reg1', default = None, type = str)
    reg_2 = request.args.get('reg2', default = None, type = str)

    if reg_1 and reg_2:
        return jsonify(get_reg_details(reg_1, reg_2))
    else:
        return 'please enter registration details as part 1 and 2'

@app.route('/captchabal')
def get_balance():
    return jsonify({"balance left":str(api.get_balance())})

if __name__ == "__main__":
    app.run(port=8000, threaded=True)
