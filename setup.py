try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Proxy test framework',
    'author': 'Thomas Jackson',
    'url': 'https://gitli.corp.linkedin.com/thjackso/proxy_test',
    #'download_url': 'Where to download it.',
    'author_email': 'thjackso@linkedin.com',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['proxy_test'],
    'scripts': [],
    'name': 'proxy_test'
}

setup(**config)
