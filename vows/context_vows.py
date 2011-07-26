#!/usr/bin/env python
# -*- coding: utf-8 -*-

# tornado-pyvows extensions
# https://github.com/rafaelcaricio/tornado-pyvows

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 Rafael Caricio rafael@caricio.com


import tornado.web

from pyvows import Vows, expect
from tornado_pyvows import TornadoHTTPContext, TornadoSubContext

from vows.test_app import MainPageHandler

@Vows.batch
class Application(TornadoHTTPContext):
    def _get_app(self):
        application = tornado.web.Application([
            (r"/", MainPageHandler),
        ])
        return application

    class HomeUrlBody(TornadoSubContext):

        def topic(self):
            return self._get('/')

        def should_be_hello_world(self, topic):
            expect(topic.body).to_equal('Hello, world')

    class WhenPostWithoutData(TornadoSubContext):

        def topic(self):
            return self._post('/')

        def the_response_should_be_ok(self, topic):
            expect(topic.code).to_equal(200)

        def the_response_should_be_json(self, topic):
            expect(topic.body).to_equal("{\"message\":\"Hello, world\"")
