#!/usr/bin/python
# -*- coding: utf-8 -*-

# tornado-pyvows extensions
# https://github.com/rafaelcaricio/tornado-pyvows

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 Rafael Caricio rafael@caricio.com

import sys
import os
import logging
import time
import contextlib
import urllib

import tornado.ioloop
from tornado.httpclient import AsyncHTTPClient
from tornado.httpserver import HTTPServer
from tornado.stack_context import NullContext
from tornado.testing import get_unused_port
from pyvows import Vows

class AsyncTestCase(object):

    def setUp(self):
        self.io_loop = self.get_new_ioloop()

    def tearDown(self):
        if self.io_loop is not tornado.ioloop.IOLoop.instance():
            for fd in self.io_loop._handlers.keys()[:]:
                if (fd == self.io_loop._waker_reader.fileno() or
                    fd == self.io_loop._waker_writer.fileno()):
                    continue
                try:
                    os.close(fd)
                except:
                    logging.debug("error closing fd %d", fd, exc_info=True)
            self.io_loop._waker_reader.close()
            self.io_loop._waker_writer.close()

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop()

    @contextlib.contextmanager
    def stack_context(self):
        try:
            yield
        except:
            self.failure = sys.exc_info()
            self.stop()

    def stop(self, _arg=None, **kwargs):
        assert _arg is None or not kwargs
        self.stop_args = kwargs or _arg
        if self.running:
            self.io_loop.stop()
            self.running = False
        self.stopped = True

    def wait(self, condition=None, timeout=5):
        if not self.stopped:
            if timeout:
                def timeout_func():
                    try:
                        raise AssertionError(
                          'Async operation timed out after %d seconds' %
                          timeout)
                    except:
                        self.failure = sys.exc_info()
                    self.stop()
                self.io_loop.add_timeout(time.time() + timeout, timeout_func)
            while True:
                self.running = True
                with NullContext():
                    self.io_loop.start()
                if (self.failure is not None or
                    condition is None or condition()):
                    break
        assert self.stopped
        self.stopped = False
        if self.failure is not None:
            raise self.failure[0], self.failure[1], self.failure[2]
        result = self.stop_args
        self.stop_args = None
        return result

class AsyncHTTPTestCase(AsyncTestCase):
    def setUp(self):
        self.stopped = False
        self.running = False
        self.failure = None
        self.stop_args = None

        super(AsyncHTTPTestCase, self).setUp()
        self.port = None

        self.http_client = AsyncHTTPClient(io_loop=self.io_loop)
        if hasattr(self, 'get_app'):
            self.app = self.get_app()
            self.http_server = HTTPServer(self.app, io_loop=self.io_loop,
                                          **self.get_httpserver_options())
            self.http_server.listen(self.get_http_port())

    def fetch(self, path, **kwargs):
        self.http_client.fetch(self.get_url(path), self.stop, **kwargs)
        return self.wait()

    def get_httpserver_options(self):
        return {}

    def get_http_port(self):
        if self.port is None:
            self.port = get_unused_port()
        return self.port

    def get_url(self, path):
        return 'http://localhost:%s%s' % (self.get_http_port(), path)

    def tearDown(self):
        self.http_server.stop()
        self.http_client.close()
        super(AsyncHTTPTestCase, self).tearDown()

class ParentAttributeMixin(object):

    def get_parent_argument(self, name):
        parent = self.parent
        while parent:
            if hasattr(parent, name):
                return getattr(parent, name)
            parent = parent.parent

        return None

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return self.get_parent_argument(name)


class TornadoContext(Vows.Context, ParentAttributeMixin, AsyncTestCase):

    def __init__(self, parent, *args, **kwargs):
        Vows.Context.__init__(self, parent)
        ParentAttributeMixin.__init__(self)
        AsyncTestCase(*args, **kwargs)

        self.setUp()
        self.ignore('get_parent_argument', 'setUp', 
                    'get_app', 'fetch', 'get_httpserver_options', 
                    'get_http_port', 'get_url', 'tearDown',
                    'get_new_ioloop', 'stack_context', 'stop', 'wait')


class TornadoHTTPContext(Vows.Context, ParentAttributeMixin, AsyncHTTPTestCase):

    def __init__(self, parent, *args, **kwargs):
        Vows.Context.__init__(self, parent)
        ParentAttributeMixin.__init__(self)
        AsyncHTTPTestCase.__init__(self, *args, **kwargs)

        self.setUp()

        self.ignore('get_parent_argument', 'setUp', 
                    'get_app', 'fetch', 'get_httpserver_options', 
                    'get_http_port', 'get_url', 'tearDown',
                    'get_new_ioloop', 'stack_context', 'stop', 'wait',
                    'get', 'post')

    def get(self, path):
        return self.fetch(path, method="GET")

    def post(self, path, data={}):
        return self.fetch(path, method="POST", body=urllib.urlencode(data, doseq=True))
