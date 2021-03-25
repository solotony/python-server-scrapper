import re
import json
import logging
import http.client
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from time import sleep

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class Converter:

    RATE_SRC_PATH = '/currency_usd.asp'
    RATE_SRC_DOMAIN = 'www.profinance.ru'
    RE_USD_RATE = re.compile(r'<b><font\scolor="Red">(\d+(?:\.\d+)?)</font></b>',
                             re.MULTILINE + re.UNICODE + re.VERBOSE)

    _rate = None

    @classmethod
    def fetch_rate(cls)->None:
        try:
            conn = http.client.HTTPSConnection(cls.RATE_SRC_DOMAIN)
            conn.request("GET", cls.RATE_SRC_PATH)
            response = conn.getresponse()
            if response.status != 200:
                logger.error('bad status: {} {}', response.status, response.reason)
                conn.close()
                return
            content = response.read().decode('utf-8')
            conn.close()
            mo = cls.RE_USD_RATE.search(content)
            if mo:
                cls._rate = float(mo[1])
                logger.info('rate={}'.format(cls._rate))
                return
            logger.error('bad source - rate not found')
        except:
            logger.exception('rate failed')

    @classmethod
    def convert(cls, x: float) -> [float, None]:
        if not cls._rate:
            return None
        return round(x * cls._rate, ndigits=2)

    @classmethod
    def get_rate(cls) -> [float, None]:
        return cls._rate


class MyHTTPRequestHandler(BaseHTTPRequestHandler):

    PORT = 7777
    SERVER = 'localhost'
    RE_CONVERT = re.compile(r'^/convert/(\d+(?:\.\d+)?)/$')
    DOCUMENTATION = documentation = '''<h1>documentation</h1>
    <pre>
    usage:
        http://{server}:{port}/convert/&lt;amount_in_usd&gt;/
        amount_in_usd integer or decimal
    example:
        <a href='http://{server}:{port}/convert/777/'>http://{server}:{port}/convert/777/</a>
        <a href='http://{server}:{port}/convert/333.33/'>http://{server}:{port}/convert/333.33/</a>
    </pre>'''.format(server=SERVER, port=PORT)

    def my_send_error(self, response_obj):
        response_js = json.dumps(response_obj)
        self.send_response(400)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(response_js.encode())

    def my_send_success(self, response_obj):
        response_js = json.dumps(response_obj)
        self.send_response(200, 'OK')
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(response_js.encode())

    def do_GET(self):
        if self.path == "/":
            self.send_response(200, 'OK')
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(self.DOCUMENTATION.encode())
            return
        if Converter.get_rate() is None:
            self.my_send_error({'errror': 'no rate'})
            return
        mo = self.RE_CONVERT.match(self.path)
        if mo:
            usd = float(mo[1])
            rub = Converter.convert(usd)
            self.my_send_success({'rate': Converter.get_rate(), 'usd': usd, 'rub':rub})
            return
        self.my_send_error({'errror': 'bad request'})


def update_rate_forever():
    while True:
        Converter.fetch_rate()
        sleep(10)

if __name__ == '__main__':
    thread = threading.Thread(target=update_rate_forever)
    thread.start()
    httpd = HTTPServer(('', MyHTTPRequestHandler.PORT), MyHTTPRequestHandler)
    httpd.serve_forever()

