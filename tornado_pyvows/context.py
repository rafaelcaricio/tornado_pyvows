#!/usr/bin/python
# -*- coding: utf-8 -*-

# tornado-pyvows extensions
# https://github.com/rafaelcaricio/tornado-pyvows

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com rafael@caricio.com

import sys
import os
import logging
import time
import contextlib

import tornado.ioloop
from tornado.httpclient import AsyncHTTPClient
from tornado.httpserver import HTTPServer
from tornado.stack_context import NullContext
from pyvows import Vows

_next_port = 10000
def get_unused_port():
    """Returns a (hopefully) unused port number."""
    global _next_port
    port = _next_port
    _next_port = _next_port + 1
    return port

class AsyncTestCase(object):

    def _setUp(self):
        self.io_loop = self._get_new_ioloop()

    def _tearDown(self):
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

    def _get_new_ioloop(self):
        return tornado.ioloop.IOLoop()

    @contextlib.contextmanager
    def _stack_context(self):
        try:
            yield
        except:
            self._failure = sys.exc_info()
            self.stop()

    def _stop(self, _arg=None, **kwargs):
        assert _arg is None or not kwargs
        self._stop_args = kwargs or _arg
        if self._running:
            self.io_loop.stop()
            self._running = False
        self._stopped = True

    def _wait(self, condition=None, timeout=5):
        if not self._stopped:
            if timeout:
                def timeout_func():
                    try:
                        raise self.failureException(
                          'Async operation timed out after %d seconds' %
                          timeout)
                    except:
                        self._failure = sys.exc_info()
                    self._stop()
                self.io_loop.add_timeout(time.time() + timeout, timeout_func)
            while True:
                self._running = True
                with NullContext():
                    self.io_loop.start()
                if (self._failure is not None or
                    condition is None or condition()):
                    break
        assert self._stopped
        self._stopped = False
        if self._failure is not None:
            raise self._failure[0], self._failure[1], self._failure[2]
        result = self._stop_args
        self._stop_args = None
        return result

class AsyncHTTPTestCase(AsyncTestCase):
    def _setUp(self):
        self._stopped = False
        self._running = False
        self._failure = None
        self._stop_args = None

        super(AsyncHTTPTestCase, self)._setUp()
        self._port = None

        self._http_client = AsyncHTTPClient(io_loop=self.io_loop)
        self._app = self._get_app()
        self._http_server = HTTPServer(self._app, io_loop=self.io_loop,
                                      **self._get_httpserver_options())
        self._http_server.listen(self._get_http_port())

    def _get_app(self):
        raise NotImplementedError()

    def _fetch(self, path, **kwargs):
        self.http_client.fetch(self.get_url(path), self._stop, **kwargs)
        return self._wait()

    def _get_httpserver_options(self):
        return {}

    def _get_http_port(self):
        if self._port is None:
            self._port = get_unused_port()
        return self._port

    def _get_url(self, path):
        return 'http://localhost:%s%s' % (self._get_http_port(), path)

    def _tearDown(self):
        self.http_server._stop()
        self.http_client.close()
        super(AsyncHTTPTestCase, self).tearDown()

class TornadoContext(Vows.Context, AsyncHTTPTestCase):
    def _get_app(self):
        raise NotImplementedError()

    def topic(self):
        self._setUp()

class TornadoSubContext(Vows.Context):
    def _get_parent_argument(self, name):
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
            return self._get_parent_argument(name)


