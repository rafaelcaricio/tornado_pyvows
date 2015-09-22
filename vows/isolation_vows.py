#!/usr/bin/python
# -*- coding: utf-8 -*-

# tornado-pyvows extensions
# https://github.com/rafaelcaricio/tornado-pyvows

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 Rafael Caricio rafael@caricio.com
from pyvows import Vows, expect
from tornado_pyvows import TornadoHTTPContext, IsolatedTornadoHTTPContext

from tornado import gen
from tornado.web import RequestHandler, asynchronous

from mock import CallableMixin, NonCallableMock


class AsyncCallableMixin(CallableMixin):
    """Change the __call__ method such that it does not return but call the
    `callback` kwarg with the return value.
    """

    def __call__(_mock_self, *args, **kwargs):
        cb = kwargs.get('callback', None)

        _mock_self._mock_check_sig(*args, **kwargs)

        if cb:
            del kwargs['callback']
            result = _mock_self._mock_call(*args, **kwargs)
            cb(result)
        else:
            return _mock_self._mock_call(*args, **kwargs)


class AsyncMock(AsyncCallableMixin, NonCallableMock):
    pass


@Vows.assertion
def has_been_called_with(mock, *args, **kwargs):
    mock.assert_called_with(*args, **kwargs)


@Vows.assertion
def has_been_called_once_with(mock, *args, **kwargs):
    mock.assert_called_once(*args, **kwargs)


@Vows.assertion
def has_any_call(mock, *args, **kwargs):
    mock.assert_any_call(*args, **kwargs)


@Vows.assertion
def has_calls(mock, calls, any_order=False):
    mock.assert_has_calls(calls, any_order=any_order)


class ExampleHandler(RequestHandler):

    @asynchronous
    @gen.engine
    def get(self):
        echo = yield gen.Task(self.echo)
        self.finish(echo)

    def echo(self, callback=None):
        callback('echo')


@Vows.batch
class ASimpleTestWithAMock(TornadoHTTPContext):

    def get_handler_spec(self):
        """..."""
        return (r'^/echo$', ExampleHandler)

    def get_application_settings(self):
        return {'debug': True}

    class AndASimpleTestCase(IsolatedTornadoHTTPContext):

        def topic(self):
            mock = AsyncMock()
            mock.return_value = 'mocked echo'
            self.get_test_handler().echo = mock

            yield (mock, self.fetch('/echo'))

        def shouldWorkAsUsual(self, topic):
            expect(topic).Not.to_be_an_error()

        def shouldReturnTheExpectedTopic(self, topic):
            (_, resp) = topic
            expect(resp.body).to_equal('mocked echo')

        class ThatBlahsBlahs(TornadoHTTPContext):

            def topic(self, topic):
                yield (topic, self.fetch('/echo'))

            def shouldReturnTheExpectedTopic(self, topic):
                (_, resp) = topic
                expect(resp.body).to_equal('mocked echo')

        class ThatBlahsAgain(ThatBlahsBlahs):

            def topic(self, topic):
                yield (topic, self.fetch('/echo'))

    class ThatHasNoSideEffects(IsolatedTornadoHTTPContext):

        def topic(self):
            yield self.fetch('/echo')

        def shouldWorkAsUsual(self, topic):
            expect(topic).Not.to_be_an_error()

        def shouldReturnTheExpectedTopic(self, resp):
            expect(resp.body).to_equal('echo')

    class ThatStillHasNoSideEffects(IsolatedTornadoHTTPContext):

        def topic(self):
            mock = AsyncMock()
            mock.return_value = 'another mocked echo'
            self.get_test_handler().echo = mock

            yield (mock, self.fetch('/echo'))

        def shouldWorkAsUsual(self, topic):
            expect(topic).Not.to_be_an_error()

        def shouldReturnTheExpectedTopic(self, topic):
            (_, resp) = topic
            expect(resp.body).to_equal('another mocked echo')

        def theMockHasBeenCalledOnce(self, topic):
            (mock, _) = topic
            expect(mock).has_been_called_with()

        def thereAreNoMoreActionsOnTheMock(self, topic):
            (mock, _) = topic
            expect(mock.call_count).to_equal(1)
