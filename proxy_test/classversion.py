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


class HeaderRewriteTests(BaseProxyTest):
    def testFabricName(self):

        import json

        def headers(request):
            '''
            Spit back the headers as a json encoded string
            '''
            assert request.headers['X-Li-Pop'] == 'PROD-ELA4'
            assert request.headers['UUID'] == '1'
            return json.dumps(dict(request.headers))

        self.http_endpoint.add_handler('/headers', headers)

        proxy_ret = requests.get('http://127.0.0.1:{0}/headers'.format(self.http_endpoint.address[1]),
                                  headers={'__COOL_TEST_KEY__': 1},
                                  proxies=BaseProxyTest.static_proxies)

        '''
        TODO: create some class which wraps the get mechanisms to add the magic header for tracking
        and will return an object which contains:
            client_request
            client_response
            server_request
            server_response


        proxy_ret, server_req = self.fakerequests.get('http://127.0.0.1:{0}/headers'.format(self.http_endpoint.address[1]),
                                                      proxies=BaseProxyTest.static_proxies)

        '''

        assert proxy_ret.status_code == 200
        # check that the response had the header
        assert proxy_ret.headers['X-Li-Pop'] == 'PROD-ELA4'

        # check that the origin saw the same header
        server_headers = proxy_ret.json()
        assert server_headers['X-Li-Pop'] == 'PROD-ELA4'




if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(HeaderRewriteTests)
    #from nose_gevented_multiprocess.nose_gevented_multiprocess import GeventedMultiProcess
    #nose.main(suite=suite, addplugins=[GeventedMultiProcess()])
    nose.main(suite=suite)
