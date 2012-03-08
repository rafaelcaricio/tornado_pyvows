#!/usr/bin/env python
# -*- coding: utf-8 -*-

# tornado-pyvows extensions
# https://github.com/rafaelcaricio/tornado-pyvows

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com rafael@caricio.com

import json

import tornado.web
from tornado.web import RequestHandler

class MainPageHandler(RequestHandler):
    def get(self):
        self.write("Hello, world")

    def post(self):
        result = {}
        for arg, value in self.request.arguments.iteritems():
            result[arg] = value.pop()

        for field_name, list_of_files in self.request.files.iteritems():
            file_dict = list_of_files.pop()
            result[field_name] = file_dict 

        self.write(json.dumps(result))
