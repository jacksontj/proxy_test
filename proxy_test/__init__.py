# TODO: some request/response class to load the various libary's implementations and allow for comparison

import gevent
import gevent.greenlet
import gevent.wsgi
import grequests
from bottle import Bottle, request, hook, response
import threading
from collections import defaultdict
import requests

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

class TrackingRequests():
    def __init__(self, endpoint):
        self.endpoint = endpoint
    def __getattr__(self, name):
        def handlerFunction(*args,**kwargs):
            # if requests doesn't have a method with this name
            if not hasattr(requests, name):
                raise AttributeError()
            func = getattr(requests, name)

            # set some kwargs

            # set the tracking header
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            key = self.endpoint.get_tracking_key()
            kwargs['headers'][self.endpoint.TRACKING_HEADER] = key

            ret = {}
            resp = func(*args, **kwargs)

            server_resp = self.endpoint.get_tracking_by_key(key)

            # TODO: implement client_request
            # TODO: create intermediate objects that you can compare
            #ret['client_request'] = None
            ret['client_response'] = resp
            ret['server_request'] = server_resp['request']
            ret['server_response'] = server_resp['response']

            return ret

            print name,args,kwargs
        return handlerFunction

# TODO: force http access log somewhere else
# TODO: no threads?
class DynamicHTTPEndpoint(threading.Thread):
    TRACKING_HEADER = '__cool_test_header__'

    @property
    def address(self):
        return self.server.address

    def __init__(self):
        threading.Thread.__init__(self)
        # dict to store request data in
        self.tracked_requests = {}

        self.daemon = True

        self.ready = threading.Event()

        # dict of pathname (no starting /) -> function
        self.handlers = {}

        self.app = Bottle()


        @self.app.hook('before_request')
        def save_request():
            '''
            If the tracking header is set, save the request
            '''
            if request.headers.get(self.TRACKING_HEADER):
                self.tracked_requests[request.headers[self.TRACKING_HEADER]] = {'request': request}


        @self.app.hook('after_request')
        def save_response():
            '''
            If the tracking header is set, save the response
            '''
            if request.headers.get(self.TRACKING_HEADER):
                self.tracked_requests[request.headers[self.TRACKING_HEADER]]['response'] = response

        @self.app.route('/', defaults={'path': ''})
        @self.app.route('/<path:path>')
        def catch_all(path=''):
            # get path key
            if path in self.handlers:
                return self.handlers[path](request)

            # return a 404 since we didn't find it
            return 'defualtreturn: ' + path + '\n'

    def get_tracking_key(self):
        '''
        Return a new key for tracking a request by key
        '''
        key = str(len(self.tracked_requests))
        self.tracked_requests[key] = {}
        return key

    def get_tracking_by_key(self, key):
        '''
        Return tracking data by key
        '''
        if key not in self.tracked_requests:
            raise Exception()
        return self.tracked_requests[key]

    def normalize_path(self, path):
        '''
        Normalize the path, since its common (and convenient) to start with / in your paths
        '''
        if path.startswith('/'):
            return path[1:]
        return path

    def add_handler(self, path, func):
        '''
        Add a new handler attached to a specific path
        '''
        path = self.normalize_path(path)
        if path in self.handlers:
            raise Exception()
        self.handlers[path] = func

    def remove_handler(self, path):
        '''
        remove a handler attached to a specific path
        '''
        path = self.normalize_path(path)
        if path not in self.handlers:
            raise Exception()
        del self.handlers[path]

    def run(self):
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
