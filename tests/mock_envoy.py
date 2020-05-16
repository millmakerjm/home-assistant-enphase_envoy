import os
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
from threading import Thread

import requests

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

class RequestType(Enum):
    UNKNOWN = 0
    INFO = 1
    PROD_JSON = 2
    API_PROD = 3
    API_INVERTERS = 4
    INVENTORY_JSON = 5

def get_free_port():
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    address, port = s.getsockname()
    s.close()
    return port

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        request_type = self._get_request_type()

        if request_type != RequestType.UNKNOWN and request_type in TestMockEnvoy.file_map:
            with open(os.path.join(THIS_DIR, TestMockEnvoy.file_map[request_type])) as file:
                data = file.read()

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=UTF-8")
                self.end_headers()
                self.wfile.write(bytearray(data, "UTF-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def _get_request_type(self):
        request_type = RequestType.UNKNOWN
        if self.path == '/info.xml':
            request_type = RequestType.INFO
        elif self.path == '/production' or self.path == '/production.json':
            request_type = RequestType.PROD_JSON
        elif self.path == '/api/v1/production':
            request_type = RequestType.API_PROD
        elif self.path == '/api/v1/production/inverters':
            request_type = RequestType.API_INVERTERS
        elif self.path == '/inventory.json':
            request_type = RequestType.INVENTORY_JSON
        return request_type


class TestMockEnvoy():
    file_map = dict()

    def __init__(self):
        self.server_port = get_free_port()
        self.mock_server = HTTPServer(('localhost', self.server_port), RequestHandler)

        self.mock_server_thread = Thread(target=self.mock_server.serve_forever)
        self.mock_server_thread.setDaemon(True)
        self.mock_server_thread.start()

    def set_file_map(self, new_file_map):
        TestMockEnvoy.file_map = new_file_map
