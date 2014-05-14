import time
import gevent
from proxy_test import DynamicHTTPEndpoint, testcase
from inspect import getmembers, isfunction

# start up endpoint
http_endpoint = DynamicHTTPEndpoint()
http_endpoint.start()

started = False
# wait for the thread to start up
while not started:
    try:
        started = http_endpoint.server.started
    except AttributeError as e:
        print 'endpoint not started', e
    time.sleep(1)


# fire off some jobs
jobs = []

# TODO: this better?
import tests
# import the tests...
for name, func in (f for f in getmembers(tests)):
    if name.startswith('test_'):
        jobs.append(gevent.spawn(func))

print 'join jobs'
gevent.joinall(jobs)

print 'end??'
