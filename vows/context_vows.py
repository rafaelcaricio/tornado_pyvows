#!/usr/bin/env python
# -*- coding: utf-8 -*-

# tornado-pyvows extensions
# https://github.com/rafaelcaricio/tornado-pyvows

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com rafael@caricio.com


import tornado.web

from pyvows import Vows, expect
from tornado_pyvows import TornadoContext, TornadoSubContext

from vows.test_app import MainPageHandler

@Vows.batch
class Application(TornadoContext):
    def _get_app(self):
        application = tornado.web.Application([
            (r"/", MainPageHandler),
        ])
        return application

    class HomeUrlBody(TornadoSubContext):

        def topic(self):
            return self._get('/').body

        def should_be_hello_world(self, topic):
            expect(topic).to_equal('Hello, world')
