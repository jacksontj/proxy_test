from nose.tools import *
import proxy_test
import proxy_test.test_cases

import requests

class ExampleTests(proxy_test.test_cases.BaseProxyTest):

    def testInternet(self):
        '''
        Some basic tests, can we hit public sites through a regular proxy
        '''
        # make sure we can hit it directly
        ret = requests.get('http://www.linkedin.com')
        assert ret.status_code == 200

        # proxy through to it
        ret = requests.get('http://www.linkedin.com', proxies=self.static_proxies)
        assert ret.status_code == 200

    def testHttpEndpoint(self):
        # create an endpoint to register
        def echo(request):
            return 'echo!'
        # add the endpoint
        self.http_endpoint.add_handler('/footest', echo)

        # use the webserver as the proxy (since we don't have one started)
        endpoint_base = 'http://127.0.0.1:{0}'.format(self.http_endpoint.address[1])


        ret = requests.get(endpoint_base + '/footest')
        assert ret.status_code == 200
        assert ret.content == 'echo!'


    def testTrackRequests(self):
        def echo(request):
            return 'echo!'

        # add the endpoint
        self.http_endpoint.add_handler('/testTrackRequests', echo)

        endpoint_base = 'http://127.0.0.1:{0}'.format(self.http_endpoint.address[1])

        tmp = self.track_requests.get(endpoint_base + '/testTrackRequests')
        assert tmp['client_response'].status_code == tmp['server_response'].status_code
        assert tmp['client_request'].url == tmp['server_request'].url

        # make sure the client_request headers are a subset of the server_request
        # (Host header doesn't show up for some reason)
        for key, val in tmp['client_request'].headers.iteritems():
            assert tmp['client_request'].headers[key] == tmp['server_request'].headers[key]

        # TODO: figure out why client_request doesn't include the host header it sends
        # https://github.com/kennethreitz/requests/issues/2060
        print dict(tmp['client_request'].headers)
        raise Exception()
