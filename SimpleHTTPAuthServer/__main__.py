'''
A simple authenticated web server handler
'''

from SimpleHTTPServer import SimpleHTTPRequestHandler
import os
import base64
import ssl
import SocketServer
import argparse

CERT_FILE = "cert.pem"
KEY_FILE = "key.pem"

class SimpleHTTPAuthHandler(SimpleHTTPRequestHandler):
    ''' Main class to present webpages and authentication. '''
    KEY = ''

    def do_HEAD(self):
        ''' head method '''
        print "send header"
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_authhead(self):
        ''' do authentication '''
        print "send header"
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Test\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        ''' Present frontpage with user authentication. '''
        if self.headers.getheader('Authorization') is None:
            self.do_authhead()
            self.wfile.write('no auth header received')
        elif self.headers.getheader('Authorization') == 'Basic '+ self.KEY:
            SimpleHTTPRequestHandler.do_GET(self)
        else:
            self.do_authhead()
            self.wfile.write(self.headers.getheader('Authorization'))
            self.wfile.write('not authenticated')

def serve_https(https_port=80, cert=True, handler_class=SimpleHTTPAuthHandler):
    ''' setting up server '''
    httpd = SocketServer.TCPServer(("", https_port), handler_class)
    if cert:
        httpd.socket = ssl.wrap_socket(httpd.socket, keyfile=KEY_FILE,
                                       certfile=CERT_FILE, server_side=True)
    socket_addr = httpd.socket.getsockname()
    print "Serving HTTP on", socket_addr[0], "port", socket_addr[1], "..."
    httpd.serve_forever()

def main():
    ''' Parsing inputs '''
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int, help='port number')
    parser.add_argument('key', help='username:password')
    parser.add_argument('--dir', required=False, help='directory')
    parser.add_argument('--cert', help='Use the provided cert', action='store_true', default=False)
    args = parser.parse_args()

    SimpleHTTPAuthHandler.KEY = base64.b64encode(args.key)

    if args.dir:
        print "Changing dir to {cd}".format(cd=args.dir)
        os.chdir(args.dir)

    serve_https(int(args.port), cert=args.cert, handler_class=SimpleHTTPAuthHandler)


if __name__ == '__main__':
    main()