import http.server, http, cgi, pathlib, sys, argparse, ssl, os, builtins,win32clipboard,tempfile
from io import BytesIO

from PIL import ImageGrab,Image,PngImagePlugin,BmpImagePlugin

# Does not seem to do be used, but leaving this import out causes uploadserver to not receive IPv4 requests when
# started with default options under Windows
import socket 

if sys.version_info.major > 3 or sys.version_info.minor >= 7:
    import functools

if sys.version_info.major > 3 or sys.version_info.minor >= 8:
    import contextlib

UPLOAD_PAGE = bytes('''<!DOCTYPE html>
<html>
<head>
<title>File Upload</title>
<meta name="viewport" content="width=device-width, user-scalable=no" />
<style type="text/css">
@media (prefers-color-scheme: dark) {
  body {
    background-color: #000;
    color: #fff;
  }
}
</style>
</head>
<body onload="document.getElementsByName('token')[0].value=localStorage.token || ''">
<h1>File Upload</h1>
<form action="upload" method="POST" enctype="multipart/form-data">
<input name="files" type="file" multiple />
<br />
<br />
Token (only needed if server was started with token option): <input name="token" type="text" />
<br />
<br />
<input type="submit" onclick="localStorage.token = document.getElementsByName('token')[0].value" />
</form>
</body>
</html>''', 'utf-8')


def send_to_clipboard(clip_type, data):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(clip_type, data)
    win32clipboard.CloseClipboard()
    
def get_clipboard():
    """returns the contents of the computer's clipboard""" 
    img= ImageGrab.grabclipboard()
    if img!=None:                                            
        if isinstance(img,list):                             #check if it is a link to a file  
            img = fr'{ImageGrab.grabclipboard()[0]}'
            try:                                             #Is it an image?
                with Image.open(img) as im:
                    output = BytesIO()
                    im.convert("RGB").save(output, "BMP")
                    data = output.getvalue()
            except Exception as er:                          #probably not an image
                print("this wasn't a valid image")
                with open(img,mode='rb') as file:
                    data=(file.read())+bytes('^*^','utf-8')
                file.close()   
                
        if isinstance(img,PngImagePlugin.PngImageFile) or isinstance(img,BmpImagePlugin.DibImageFile): #An image taken with snipingtool or WIN+SHIFT+S
            output = BytesIO()
            img.convert("RGB").save(output, "BMP")
            data = output.getvalue()
            
        
            
            
            
    else:
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        data=bytes(data+'^*^','utf-8') #
        print ("The data is :",data)
        
    return data

def send_upload_page(handler):
    handler.send_response(http.HTTPStatus.OK)
    handler.send_header('Content-Type', 'application/octet-stream; charset=utf-8')
    handler.send_header('Content-Length', len(UPLOAD_PAGE))
    handler.end_headers()
    handler.wfile.write(UPLOAD_PAGE)

def receive_upload(handler):
    result = (http.HTTPStatus.INTERNAL_SERVER_ERROR, 'Server error')
    form = cgi.FieldStorage(fp=handler.rfile, headers=handler.headers, environ={'REQUEST_METHOD': 'POST'})
    if args.token:
        # server started with token.
        if 'token' not in form or form['token'].value != args.token:
            # no token or token error
            return (http.HTTPStatus.FORBIDDEN, f'Token is enabled on this server, and your token : {form["token"].value} is wrong')
        
    known_fields=['files','copy','url','browser','clip','cpimage']
    good_field=False                    #We assume we don't find any good fields at first
    for field in known_fields:
        if field in form:
            good_field=True             #We found at least one good field
    if not good_field:
        return (http.HTTPStatus.BAD_REQUEST, f'None of these known fields have been found : {known_fields}')
    
    
    
    if 'clip' in form:
        """Returns the contents of this computer's clipboard to the requestor, this can be an image,videos or any binary content."""
        handler.wfile.flush()
        data=get_clipboard()
        handler.wfile.write(data)
        result = (http.HTTPStatus.NO_CONTENT, None)
        return result

    if 'copy' in form:
        """Copies to the clipboard of this computer the content received in the request"""
        fields = form['copy']
        content=fields.value
        print("\n\n",content,"\n\nSent to the Clipboard!`\n\n")
        send_to_clipboard(win32clipboard.CF_UNICODETEXT, content)
        result = (http.HTTPStatus.NO_CONTENT, None)
        return result

    if 'url' in form:
        """same as 'copy' but the content is a URL where the '/' character has been replaced by '^' to be able to pass in the request and needs to be fixed """
        fields = form['url']
        content=fields.filename[:-4].replace("^","/")
        print("\n\n",content,"\n\nSent to the Clipboard!`\n\n")
        send_to_clipboard(win32clipboard.CF_UNICODETEXT, content)
        result = (http.HTTPStatus.NO_CONTENT, None)
        return result

    if 'browser' in form:
        """same as 'url' but instead of copying the url to the clipboard the url is opened in the default browser of this computer"""
        fields = form['browser']
        content=fields.filename[:-4].replace("^","/").replace('&','"&"') #cmd understand '&' as a specific command we need to escape it 
        result = (http.HTTPStatus.NO_CONTENT, None)
        if 'http' not in content:
            print(f"\n\nThis doesn't look like a web url :\n\n{content}")
            
            return result
        
        print(content)
        os.system(f"start {content}")
        
        return result

    if 'cpimage' in form:
        """Sends the image sent by the requestor to the clipboard if possible, not all formats are supported """
        field = form['cpimage']
        data=field.file.file.read()
        try :
            f = tempfile.TemporaryFile()
            f.write(data)
            img=Image.open(f)
            output = BytesIO()
            img.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()
            send_to_clipboard(win32clipboard.CF_DIB, data)
        except Exception as Error:
            print("The content received can't be used as an image",Error)
        f.close()
        
        
        
        
        result = (http.HTTPStatus.NO_CONTENT, None)
        return result
    

    if "files" in form:
        """saves the file sent by the requestor in the working folder of the http server"""
        fields = form['files']
        if not isinstance(fields, list):
            fields = [fields]
        
        for field in fields:
            if field.file and field.filename:
                filename = pathlib.Path(field.filename).name
            else:
                filename = None
            
            if filename:
                with open(pathlib.Path(args.directory) / filename, 'wb') as f:
                    f.write(field.file.read())
                    handler.log_message('Upload of "{}" accepted'.format(filename))
                    result = (http.HTTPStatus.NO_CONTENT, None)
    
    return result

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/upload': send_upload_page(self)
        else: http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        if self.path == '/upload':
            result = receive_upload(self)
            if result[0] < http.HTTPStatus.BAD_REQUEST:
                self.send_response(result[0], result[1])
                self.end_headers()
            else:
                self.send_error(result[0], result[1])
        else:
            self.send_error(http.HTTPStatus.NOT_FOUND, 'Can only POST to /upload')

class CGIHTTPRequestHandler(http.server.CGIHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/upload': send_upload_page(self)
        else: http.server.CGIHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        if self.path == '/upload':
            result = receive_upload(self)
            if result[0] < http.HTTPStatus.BAD_REQUEST:
                self.send_response(result[0], result[1])
                self.end_headers()
            else:
                self.send_error(result[0], result[1])
        else:
            http.server.CGIHTTPRequestHandler.do_POST(self)

def intercept_first_print():
    if args.server_certificate:
        # Use the right protocol in the first print call in case of HTTPS
        old_print = builtins.print
        def new_print(*args, **kwargs):
            old_print(args[0].replace('HTTP', 'HTTPS').replace('http', 'https'), **kwargs)
            builtins.print = old_print
        builtins.print = new_print

def ssl_wrap(socket):
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    server_root = pathlib.Path(args.directory).resolve()
    
    # Server certificate handling
    server_certificate = pathlib.Path(args.server_certificate).resolve()
    
    if not server_certificate.is_file():
        print('Server certificate "{}" not found, exiting'.format(server_certificate))
        sys.exit(4)
    
    if server_root in server_certificate.parents:
        print('Server certificate "{}" is inside web server root "{}", exiting'.format(server_certificate, server_root))
        sys.exit(3)
    
    context.load_cert_chain(certfile=server_certificate)
    
    if args.client_certificate:
        # Client certificate handling
        client_certificate = pathlib.Path(args.client_certificate).resolve()
        
        if not client_certificate.is_file():
            print('Client certificate "{}" not found, exiting'.format(client_certificate))
            sys.exit(4)
        
        if server_root in client_certificate.parents:
            print('Client certificate "{}" is inside web server root "{}", exiting'.format(client_certificate, server_root))
            sys.exit(3)
    
        context.load_verify_locations(cafile=client_certificate)
        context.verify_mode = ssl.CERT_REQUIRED
    
    try:
        return context.wrap_socket(socket, server_side=True)
    except ssl.SSLError as e:
        print('SSL error: "{}", exiting'.format(e))
        sys.exit(5)

def serve_forever():
    # Verify arguments in case the method was called directly
    assert hasattr(args, 'port') and type(args.port) is int
    assert hasattr(args, 'cgi') and type(args.cgi) is bool
    assert hasattr(args, 'bind')
    assert hasattr(args, 'token')
    assert hasattr(args, 'server_certificate')
    assert hasattr(args, 'client_certificate')
    assert hasattr(args, 'directory') and type(args.directory) is str
    
    if args.cgi:
        handler_class = CGIHTTPRequestHandler
    elif sys.version_info.major == 3 and sys.version_info.minor < 7:
        handler_class = SimpleHTTPRequestHandler
    else:
        handler_class = functools.partial(SimpleHTTPRequestHandler, directory=args.directory)
    
    print('File upload available at /upload')
    
    if sys.version_info.major == 3 and sys.version_info.minor < 8:
        # The only difference in http.server.test() between Python 3.6 and 3.7 is the default value of ServerClass
        if sys.version_info.minor < 7:
            from http.server import HTTPServer as DefaultHTTPServer
        else:
            from http.server import ThreadingHTTPServer as DefaultHTTPServer
        
        class CustomHTTPServer(DefaultHTTPServer):
            def server_bind(self):
                bind = super().server_bind()
                if args.server_certificate:
                    self.socket = ssl_wrap(self.socket)
                return bind
        server_class = CustomHTTPServer
    else:
        class DualStackServer(http.server.ThreadingHTTPServer):
            def server_bind(self):
                # suppress exception when protocol is IPv4
                with contextlib.suppress(Exception):
                    self.socket.setsockopt(
                        socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                bind = super().server_bind()
                if args.server_certificate:
                    self.socket = ssl_wrap(self.socket)
                return bind
        server_class = DualStackServer
    
    intercept_first_print()
    http.server.test(
        HandlerClass=handler_class,
        ServerClass=server_class,
        port=args.port,
        bind=args.bind,
    )

def main():
    global args
    
    # In Python 3.8, http.server.test() was altered to use None instead of '' as the default for its bind parameter
    if sys.version_info.major == 3 and sys.version_info.minor < 8:
        bind_default = ''
    else:
        bind_default = None
    
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int, default=8000, nargs='?',
        help='Specify alternate port [default: 8000]')
    parser.add_argument('--cgi', action='store_true',
        help='Run as CGI Server')
    parser.add_argument('--bind', '-b', default=bind_default, metavar='ADDRESS',
        help='Specify alternate bind address [default: all interfaces]')
    parser.add_argument('--token', '-t', type=str,
        help='Specify alternate token [default: \'\']')
    parser.add_argument('--server-certificate', '--certificate', '-c',
        help='Specify HTTPS server certificate to use [default: none]')
    parser.add_argument('--client-certificate',
        help='Specify HTTPS client certificate to accept for mutual TLS [default: none]')
    
    # Directory option was added to http.server in Python 3.7
    if sys.version_info.major > 3 or sys.version_info.minor >= 7:
        parser.add_argument('--directory', '-d', default=os.getcwd(),
            help='Specify alternative directory [default:current directory]')
    
    args = parser.parse_args()
    if not hasattr(args, 'directory'): args.directory = os.getcwd()
    
    serve_forever()
