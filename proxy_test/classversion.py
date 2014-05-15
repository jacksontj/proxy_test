'''
TODO: parallelize nosetest runs with gevent plugin
    https://groups.google.com/forum/#!topic/nose-users/8JgyeMiWGnA
'''
import nose
import unittest


import time
import proxy_test
import requests

from collections import defaultdict


# some Globals
REQUEST_ID_HEADER = 'X-Request-Id'


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
        self.http_endpoint = proxy_test.DynamicHTTPEndpoint()
        self.http_endpoint.start()

        self.http_endpoint.ready.wait()

        # create local requester object
        self.track_requests = proxy_test.TrackingRequests(self.http_endpoint)

    def tearDown(self):
        '''
        Kill the tests that are in flight?
        '''
        pass

    # TODO: some function to get request/response x4 for everything
    # for now i'll leave it up to you


class ExampleTests(BaseProxyTest):
    def testInternet(self):
        '''
        Some basic tests, can we hit public sites through a regular proxy
        '''
        # make sure we can hit it directly
        # TODO: make this less ugly, some helper function/class
        ret = requests.get('http://www.linkedin.com')
        assert ret.status_code == 200

        # proxy through it
        ret = requests.get('http://www.linkedin.com', proxies=BaseProxyTest.static_proxies)
        assert ret.status_code == 200

    def testEcho(self):
        # create an endpoint to register
        def echo(request):
            return 'echo!'
        # add the endpoint
        self.http_endpoint.add_handler('/footest', echo)

        proxy_ret = requests.get('http://127.0.0.1:{0}/footest'.format(self.http_endpoint.address[1]),
                                  proxies=BaseProxyTest.static_proxies)
        assert proxy_ret.status_code == 200

        tmp = self.track_requests.get('http://127.0.0.1:{0}/footest'.format(self.http_endpoint.address[1]),
                                      proxies=BaseProxyTest.static_proxies)
        assert tmp['client_response'].status_code == tmp['server_response'].status_code
        # make sure no one changed the headers
        # server_response headers are empty, since we didn't set any
        #assert dict(tmp['client_response'].headers) == dict(tmp['server_response'].headers)


class HeaderRewriteTests(BaseProxyTest):
    def testFabricName(self):

        import json

        def headers(request):
            return 'echo'

        self.http_endpoint.add_handler('/headers', headers)

        track_ret = self.track_requests.get('http://127.0.0.1:{0}/headers'.format(self.http_endpoint.address[1]),
                                             proxies=BaseProxyTest.static_proxies)

        HEADER_KEY = 'X-Li-Pop'
        HEADER_VALUE = 'PROD-ELA4'

        assert track_ret['server_request'].headers[HEADER_KEY] == HEADER_VALUE
        assert track_ret['server_response'].headers[HEADER_KEY] == HEADER_VALUE
        assert track_ret['client_response'].headers[HEADER_KEY] == HEADER_VALUE




if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(ExampleTests)
    #from nose_gevented_multiprocess.nose_gevented_multiprocess import GeventedMultiProcess
    #nose.main(suite=suite, addplugins=[GeventedMultiProcess()])
    nose.main(suite=suite)
