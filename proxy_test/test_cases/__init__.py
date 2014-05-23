'''
TODO: parallelize nosetest runs with gevent plugin
    https://groups.google.com/forum/#!topic/nose-users/8JgyeMiWGnA
'''
import nose

# Support python 2.6
import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


import time
import proxy_test
import requests



class BaseProxyTest(unittest.TestCase):
    # configuration options that will be shared amongst the test cases.
    # primarily where the proxy is

    # if we configure an open proxy, we can just overwrite the IP/port but leave host headers etc
    static_proxies = {
      'http': 'http://127.0.0.1:8081',
      'https': 'http://127.0.0.1:8081',
    }

    @classmethod
    def setUpClass(cls):
        '''
        Start up your own endpoint
        '''
        cls.http_endpoint = proxy_test.DynamicHTTPEndpoint()
        cls.http_endpoint.start()

        cls.http_endpoint.ready.wait()

        # create local requester object
        cls.track_requests = proxy_test.TrackingRequests(cls.http_endpoint)

    @classmethod
    def tearDownClass(cls):
        pass


class ExampleTests(BaseProxyTest):
    def testInternet(self):
        '''
        Some basic tests, can we hit public sites through a regular proxy
        '''
        # make sure we can hit it directly
        ret = requests.get('http://www.linkedin.com')
        assert ret.status_code == 200

        # proxy through to it
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
