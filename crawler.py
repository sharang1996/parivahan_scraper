import requests
from bs4 import BeautifulSoup

def create_session(reg_no_1, reg_no_2):

    sess = requests.session()

    resp = sess.get('https://parivahan.gov.in/rcdlstatus/')

    soup = BeautifulSoup(resp.content, 'lxml')

    img_req = sess.get('https://parivahan.gov.in/rcdlstatus/DispplayCaptcha', verify=False)

    #img_text = pytesseract.image_to_string(img)

    with open('img.png', 'wb')as f:
        f.write(img_req.content)

    img_text = input('enter captcha value!')
    print(img_text)

    data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'form_rcdl:j_idt43',
            'javax.faces.partial.execute': '@all',
            'javax.faces.partial.render': 'form_rcdl:pnl_show form_rcdl:pg_show form_rcdl:rcdl_pnl',
            'form_rcdl:j_idt43': 'form_rcdl:j_idt43',
            'form_rcdl': 'form_rcdl',
            'form_rcdl:tf_reg_no1': reg_no_1,
            'form_rcdl:tf_reg_no2': reg_no_2,
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

    print(d)

create_session('GJ01HZ', '7422')
