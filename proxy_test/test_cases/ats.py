from proxy_test.test_cases import BaseProxyTest


import requests
import subprocess
import os
import socket

class ATSDynamicTest(BaseProxyTest):
    '''
    This class will start/stop trafficserver instances for you, and apply
    any configuration overrides that you may have
    '''

    @property
    def ats_proxies(self):
        return {'http': 'http://127.0.0.2:12271',
                'https': 'http://127.0.0.2:12271'}

    @classmethod
    def setUpClass(cls):
        '''
        Start up your own ats instance
        '''
        super(ATSDynamicTest, cls).setUpClass()

        # TODO: create your own config root
        # TODO: copy/template over the configs (with overrides)
        # start up trafficserver
        env = os.environ.copy()
        env['TS_ROOT'] = '/tmp/ats_test'

        # TODO: bind to different loop back ips instead of seperate ports

        # TODO: redirect stdin/stdout
        cls.ats = subprocess.Popen(['/usr/local/bin/traffic_server'], #, '-T', '.*'],
                                   env=env)

        # TODO: timeout, if it won't start up
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                print 'attempt to connect'
                s.connect(('127.0.0.2', 12271))
                s.close()
                break
            except:
                time.sleep(0.001)


    @classmethod
    def tearDownClass(cls):
        '''
        stop the ats instance you started
        '''
        super(ATSDynamicTest, cls).setUpClass()
        cls.ats.kill()
        cls.ats.wait()

    def testInternet(self):
        '''
        Some basic tests, can we hit public sites through our dynamiclly started proxy
        '''
        # make sure we can hit it directly
        ret = requests.get('http://www.linkedin.com')
        assert ret.status_code == 200

        # proxy through to it
        ret = requests.get('http://www.linkedin.com', proxies=self.ats_proxies)
        assert ret.status_code == 200

    def testEcho(self):
        def echo(request):
            return 'echo!'
        # add the endpoint
        self.http_endpoint.add_handler('/footest', echo)

        proxy_ret = requests.get('http://127.0.0.1:{0}/footest'.format(self.http_endpoint.address[1]),
                                  proxies=self.ats_proxies)
        assert proxy_ret.status_code == 200

        tmp = self.track_requests.get('http://127.0.0.1:{0}/footest'.format(self.http_endpoint.address[1]),
                                      proxies=self.ats_proxies)
        assert tmp['client_response'].status_code == tmp['server_response'].status_code


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(ATSDynamicTest)
    #from nose_gevented_multiprocess.nose_gevented_multiprocess import GeventedMultiProcess
    #nose.main(suite=suite, addplugins=[GeventedMultiProcess()])
    nose.main(suite=suite)
