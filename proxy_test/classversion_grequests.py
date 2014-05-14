'''
TODO: parallelize nosetest runs with gevent plugin
    https://groups.google.com/forum/#!topic/nose-users/8JgyeMiWGnA
'''
import nose
import unittest


import time
import proxy_test
import requests

import grequests

from collections import defaultdict


# some Globals
REQUEST_ID_HEADER = 'X-Request-Id'
TEST_MODULE_HEADER = 'X-Test-Module'
TEST_FUNCTION_HEADER = 'X-Test-Function'


class BaseProxyTest(unittest.TestCase):
    # configuration options that will be shared amongst the test cases.
    # primarily where the proxy is

    # if we configure an open proxy, we can just overwrite the IP/port but leave host headers etc
    static_proxies = {
      'http': 'http://127.0.0.1:8081',
      'https': 'http://127.0.0.1:8081',
    }

    # TODO: dynamic proxies? Something that can spin up/tear down proxies

    def setUp(self):
        '''
        Start up your own endpoint
        '''
        # create the variables keep track of endpoints
        # dict of testid -> {client_request, client_response}
        self.requests = defaultdict(dict)

        # TODO: pass down a port? Or dynamically allocate one (or both)
        self.http_endpoint = proxy_test.DynamicHTTPEndpoint(self.requests)
        self.http_endpoint.start()

        self.http_endpoint.ready.wait()

    def tearDown(self):
        '''
        Kill the tests that are in flight?
        '''
        pass

    # TODO: some function to get request/response x4 for everything


class ExampleTests(BaseProxyTest):
    _multiprocess_shared_ = True
    def testInternet(self):
        '''
        Some basic tests, can we hit public sites through a regular proxy
        '''
        # make sure we can hit it directly
        # TODO: make this less ugly, some helper function/class
        ret = grequests.send(grequests.get('http://www.linkedin.com'))
        ret.join()
        ret = ret.get()
        assert ret.status_code == 200

        # proxy through it
        ret = grequests.send(grequests.get('http://www.linkedin.com', proxies=BaseProxyTest.static_proxies))
        ret.join()
        ret = ret.get()
        assert ret.status_code == 200

    def testEcho(self):
        return
        # create an endpoint to register
        def echo(request):
            return 'echo!', 200
        # add the endpoint
        self.http_endpoint.add_handler('/footest', echo)

        proxy_ret = requests.get('http://localhost:{0}/footest'.format(self.http_endpoint.address[1]),
                                  proxies=BaseProxyTest.static_proxies)
        assert proxy_ret.status_code == 200

class ExampleTests2(ExampleTests):
    pass



if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(ExampleTests)
    #from nose_gevented_multiprocess.nose_gevented_multiprocess import GeventedMultiProcess
    nose.main(suite=suite)#, addplugins=[GeventedMultiProcess()])
