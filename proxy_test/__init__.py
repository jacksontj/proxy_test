# TODO: some request/response class to load the various libary's implementations and allow for comparison

import gevent
import gevent.greenlet
import gevent.wsgi
import grequests
from bottle import Bottle, request, Response
import threading
from collections import defaultdict

import inspect

# dict of testid -> {client_request, client_response}
REQUESTS = defaultdict(dict)

REQUEST_ID_HEADER = 'X-Request-Id'
TEST_MODULE_HEADER = 'X-Test-Module'
TEST_FUNCTION_HEADER = 'X-Test-Function'


class register_endpoint(object):
    '''
    Decorator that allows you to dynamically register endpoints within your test
    '''
    # (file, function) -> {path -> endpoint}
    function_endpoint_map = defaultdict(dict)

    def __init__(self, endpoint_map):
        self.endpoint_map = endpoint_map

    def __call__(self, function):
        '''
        The decorator is "__call__"d with the function, we take that function
        and determine which module and function name it is to store in the
        class wide depandancy_dict
        '''
        module = inspect.getmodule(inspect.stack()[1][0])
        key = (module.__name__, function.__name__)
        self.function_endpoint_map[key] = self.endpoint_map

        return function

class testcase(object):
    '''
    Decorator used to decorate a function as a testcase
    '''
    functions = []

    def __init__(self, function):
        self.functions.append(function)


# TODO: force http access log somewhere else
# TODO: no threads?
class DynamicHTTPEndpoint(threading.Thread):
    @property
    def address(self):
        return self.server.address

    def __init__(self, requests):
        threading.Thread.__init__(self)
        self.daemon = True

        self.ready = threading.Event()

        # ref to the test case's dict of requests
        self.requests = requests
        # dict of pathname -> function
        self.handlers = {}

        self.app = Bottle()


        @self.app.route('/', defaults={'path': ''})
        @self.app.route('/<path:path>')
        def catch_all(path):
            # TODO: keep track of these
            # TODO: deepcopy?
            # update the TESTS dict with the request
            #self.requests[request.headers[REQUEST_ID_HEADER]]['server_request'] = 1 #request

            # get path key
            if path in self.handlers:
                return self.handlers[path](request)

            # return a 404 since we didn't find it
            return 'defualtreturn: ' + path + '\n', 404

    def normalize_path(self, path):
        if path.startswith('/'):
            return path[1:]
        return path

    def add_handler(self, path, func):
        path = self.normalize_path(path)
        if path in self.handlers:
            raise Exception()
        self.handlers[path] = func

    def remove_handler(self, path):
        path = self.normalize_path(path)
        if path not in self.handlers:
            raise Exception()
        del self.handlers[path]

    def run(self):
        # TODO: port for the config
        self.server = gevent.wsgi.WSGIServer(('', 0),
                                              self.app.wsgi)
        self.server.start()
        # mark it as ready
        self.ready.set()
        # serve it
        try:
            self.server._stop_event.wait()
        finally:
            gevent.greenlet.Greenlet.spawn(self.server.stop).join()

# TODO: use
# helper function to make test writing cleaner
def send_request(req):
    '''
    Send the response and return a list of the request/response on both ends
    '''
    # TODO: verify that its a grequests object?

    # TODO: add the test_id to the request
    request_id = str(len(REQUESTS) + 1)

    # make sure we have header dict
    if 'headers' not in req.kwargs:
        req.kwargs['headers'] = {}
    req.kwargs['headers'][REQUEST_ID_HEADER] =  request_id
    req.kwargs['headers'][TEST_MODULE_HEADER] =  inspect.getmodule(inspect.stack()[1][0]).__name__
    req.kwargs['headers'][TEST_FUNCTION_HEADER] =  inspect.stack()[1][3]

    # add the testid to the request
    REQUESTS[request_id] = {'client_request': req}

    request_greenlet = grequests.send(req)
    request_greenlet.join()
    client_response = request_greenlet.get()

    REQUESTS[request_id]['client_response'] = client_response
    return REQUESTS[request_id]
