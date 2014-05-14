import grequests
from proxy_test import register_endpoint, send_request, testcase

# TODO: dynamic endpoint addition from within these functions
def echo(request):
    return 'echo!'

def echo1(request):
    return 'echo1!'

@register_endpoint({'echo/': echo})
def test_http2():
    req_res_map = send_request(grequests.get('http://127.0.0.1:12346/echo/'))
    print req_res_map['client_response'].content


# this is a test
@register_endpoint({'echo/': echo1})
def test_http():
    req_res_map = send_request(grequests.get('http://127.0.0.1:12346/echo/'))

    print req_res_map

    response = req_res_map['client_response']

    print 'request', req_res_map['client_request'] == req_res_map['server_request']
    print 'response', req_res_map['client_response'] == req_res_map['server_response']

    print response.headers
    print response.content

