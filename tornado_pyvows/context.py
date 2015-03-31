#!/usr/bin/python
# -*- coding: utf-8 -*-

# tornado-pyvows extensions
# https://github.com/rafaelcaricio/tornado-pyvows

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 Rafael Caricio rafael@caricio.com

import sys
import time
import contextlib
import urllib

import tornado.ioloop
from tornado.httpclient import AsyncHTTPClient
from tornado.httpserver import HTTPServer
from tornado.stack_context import NullContext
from tornado.testing import get_unused_port
from tornado.web import Application, URLSpec
from pyvows import Vows

from urllib3.filepost import encode_multipart_formdata


class AsyncTestCase(object):

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()

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
                            timeout
                        )
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
    def initialize_ioloop(self):
        self.io_loop = self.get_new_ioloop()
        self.http_client = AsyncHTTPClient(io_loop=self.io_loop)

    def setup(self):
        self.stopped = False
        self.running = False
        self.failure = None
        self.stop_args = None

        if 'get_app' in dir(self.__class__):
            self.initialize_ioloop()
            self.app = self.get_app()
        elif hasattr(self, 'get_handler_spec') and self.get_handler_spec:
            spec = self.get_handler_spec()
            if spec:
                if isinstance(spec, tuple):
                    if len(spec) == 3:
                        (pattern, handler, kwargs) = spec
                    elif len(spec) == 2:
                        (pattern, handler) = spec
                        kwargs = {}
                elif isinstance(spec, URLSpec):
                    pattern = spec.regex.pattern
                    handler = spec.handler_class
                    kwargs = spec.kwargs

                # create an isolated version of the handler
                self.isolated_handler = type('IsolatedHandler', (handler,), {})

                self.initialize_ioloop()

                self.app = Application([
                    (pattern, self.isolated_handler, kwargs)
                ], self.get_application_settings())

        if self.app:
            self.port = get_unused_port()
            self.http_server = HTTPServer(
                self.app,
                io_loop=self.io_loop,
                **self.get_httpserver_options()
            )
            self.http_server.listen(self.port, address="0.0.0.0")

    def fetch(self, path, **kwargs):
        """
        Simple wrapper around ``http_client``. If the given ``path`` doesn't
        start with 'http' than ``path`` is passed on to the
        ``http_client.fetch``
        """
        self.http_client.fetch(self.get_url(path), self.stop, **kwargs)
        return self.wait()

    def get_httpserver_options(self):
        return {}

    def get_url(self, path):
        if not path.startswith('http'):
            return 'http://localhost:%s%s' % (self.port, path)
        return path

    def teardown(self):
        if 'http_server' in dir(self.__class__):
            self.http_server.stop()
        if 'http_client' in dir(self.__class__):
            self.http_client.close()


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


class TornadoContext(Vows.Context, AsyncTestCase, ParentAttributeMixin):

    def __init__(self, parent, *args, **kwargs):
        Vows.Context.__init__(self, parent)
        ParentAttributeMixin.__init__(self)
        AsyncTestCase(*args, **kwargs)

        super(TornadoContext, self).ignore(
            'get_parent_argument',
            'get_app', 'fetch', 'get_httpserver_options',
            'get_url', 'initialize_ioloop',
            'get_new_ioloop', 'stack_context', 'stop', 'wait'
        )


class TornadoHTTPContext(Vows.Context, AsyncHTTPTestCase, ParentAttributeMixin):

    def __init__(self, parent, *args, **kwargs):
        Vows.Context.__init__(self, parent)
        ParentAttributeMixin.__init__(self)
        AsyncHTTPTestCase.__init__(self, *args, **kwargs)

        super(TornadoHTTPContext, self).ignore(
            'get_parent_argument',
            'get_app', 'fetch', 'get_httpserver_options',
            'get_url', 'get_new_ioloop', 'stack_context', 'stop',
            'wait', 'get', 'post', 'delete', 'head', 'put',
            'get_handler_spec', 'get_application_settings',
            'get_test_handler', 'initialize_ioloop'
        )

    def setup(self):
        AsyncHTTPTestCase.setup(self)

    def teardown(self):
        AsyncHTTPTestCase.teardown(self)

    def get_handler_spec(self):
        return None

    def get_application_settings(self):
        return None

    def get_test_handler(self):
        return self.isolated_handler

    def get(self, path, **kwargs):
        return self.fetch(path, method="GET", **kwargs)

    def delete(self, path, **kwargs):
        return self.fetch(path, method="DELETE")

    def put(self, path, **kwargs):
        return self.fetch(path, method="PUT", **kwargs)

    def head(self, path, **kwargs):
        return self.fetch(path, method="HEAD", **kwargs)

    def post(self, path, data={}, multipart=False, **kwargs):
        """
        Convenience wrapper for the ``http_client``.

        :param multipart:
            If True the given ``data`` is encoded "multipart/form-data" through
            ``urllib3``
            If the value is a tuple of two elements, then the first element is
            treated as the filename of the form-data section.
        """
        body = None
        headers = {}
        if multipart:
            body, content_type = encode_multipart_formdata(data)
            headers["Content-Type"] = content_type
        else:
            body = urllib.urlencode(data, doseq=True)

        if 'headers' in kwargs:
            kwargs['headers'].update(headers)

        return self.fetch(
            path,
            method="POST",
            body=body,
            headers=headers,
            **kwargs
        )


class IsolatedTornadoHTTPContext(TornadoHTTPContext):

    def get_handler_spec(self):
        return self.get_parent_argument('get_handler_spec')()

    def get_application_settings(self):
        return self.get_parent_argument('get_application_settings')()
