#!/usr/bin/env python
# -*- coding: utf-8 -*-

# tornado-pyvows extensions
# https://github.com/rafaelcaricio/tornado-pyvows

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 Rafael Caricio rafael@caricio.com
import tornado
from tornado_pyvows import TornadoHTTPContext
from pyvows import Vows, expect

class HomeHandler(tornado.web.RequestHandler):
    
    def get(self):
        self.write("hello_world")

    def post(self):
        self.write("hello_world")


@Vows.batch
class SomeVows(TornadoHTTPContext):

    def get_app(self):
        application = tornado.web.Application([
            (r"/", HomeHandler),
        ])
        return application

    class HomeUrl(TornadoHTTPContext):
        def topic(self):
            self.http_client.fetch(self.get_url('/'), self.stop)
            response = self.wait()
            return response.body

        def should_be_hello_world(self, topic):
            expect(topic).to_equal("hello_world")

    class SameUrl(HomeUrl):
        def topic(self):
            """
            For convenience you can also use ``get`` and ``post`` to wrap the 
            calls to the ``http_client``.
            """
            response = self.get("/")
            return response.body

    class SimplePost(HomeUrl):
        def topic(self):
            response = self.post("/")
            return response.body
