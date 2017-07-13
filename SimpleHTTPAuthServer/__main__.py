'''
A simple authenticated web server handler
'''

from SimpleHTTPServer import SimpleHTTPRequestHandler
import cgi
import urllib
import time
import os
import sys
import base64
import ssl
import SocketServer
import argparse
from StringIO import StringIO

from . import __prog__

CERT_FILE = os.path.expanduser("~/.ssh/cert.pem")
KEY_FILE = os.path.expanduser("~/.ssh/key.pem")
SSL_CMD = "openssl req -newkey rsa:2048 -new -nodes -x509 "\
            "-days 3650 -keyout {0} -out {1}".format(KEY_FILE, CERT_FILE)

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

    def list_directory(self, path):
        try:
            flist = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        flist.sort(key=lambda a: os.path.getmtime(os.path.join(path, a)), reverse=True)
        f = StringIO()
        displaypath = cgi.escape(urllib.unquote(self.path))
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Directory listing for %s</title>\n" % displaypath)
        f.write("<body>\n<h2>Directory listing for %s</h2>\n" % displaypath)
        f.write("<hr>\n<ul>\n")
        for name in flist:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            date_modified = time.ctime(os.path.getmtime(fullname))
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            f.write('<li><a href="%s">%s - %s</a>\n'
                    % (urllib.quote(linkname), cgi.escape(displayname), date_modified))
        f.write("</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        encoding = sys.getfilesystemencoding()
        self.send_header("Content-type", "text/html; charset=%s" % encoding)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f


def serve_https(https_port=80, https=True, start_dir=None, handler_class=SimpleHTTPAuthHandler):
    ''' setting up server '''
    httpd = SocketServer.TCPServer(("", https_port), handler_class)

    if https:
        httpd.socket = ssl.wrap_socket(httpd.socket, keyfile=KEY_FILE,
                                       certfile=CERT_FILE, server_side=True)

    if start_dir:
        print "Changing dir to {cd}".format(cd=start_dir)
        os.chdir(start_dir)

    socket_addr = httpd.socket.getsockname()
    print "Serving HTTP on", socket_addr[0], "port", socket_addr[1], "..."
    httpd.serve_forever()

def main():
    ''' Parsing inputs '''
    parser = argparse.ArgumentParser(prog=__prog__)
    parser.add_argument('port', type=int, help='port number')
    parser.add_argument('key', help='username:password')
    parser.add_argument('--dir', required=False, help='directory')
    parser.add_argument('--https', help='Use https', action='store_true', default=False)
    args = parser.parse_args()

    if args.https:
        if not (os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE)):
            print >>sys.stderr
            print >>sys.stderr, "Missing {} or {}".format(CERT_FILE, KEY_FILE)
            print >>sys.stderr, "Run `{}`".format(SSL_CMD)
            print >>sys.stderr
            sys.exit(1)

    SimpleHTTPAuthHandler.KEY = base64.b64encode(args.key)

    serve_https(int(args.port), https=args.https,
                start_dir=args.dir, handler_class=SimpleHTTPAuthHandler)


if __name__ == '__main__':
    main()
