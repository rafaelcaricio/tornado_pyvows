#!/usr/bin/env python
# -*- coding: utf-8 -*-

# tornado-pyvows extensions
# https://github.com/rafaelcaricio/tornado-pyvows

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 Rafael Caricio rafael@caricio.com

import json

import tornado.web

from pyvows import Vows, expect
from tornado_pyvows import TornadoHTTPContext

from vows.test_app import MainPageHandler

@Vows.batch
class Application(TornadoHTTPContext):
    def get_app(self):
        application = tornado.web.Application([
            (r"/", MainPageHandler),
        ])
        return application

    class GoodRequest(TornadoHTTPContext):

        def topic(self):
            return (200, None, self.get('/'))

        def the_response_should_be_ok(self, topic):
            expected_code, _, response = topic
            expect(response.code).to_equal(expected_code)

    class HomeUrlBody(GoodRequest):

        def should_be_hello_world(self, topic):
            _, _, response = topic
            expect(response.body).to_equal('Hello, world')

    class WhenPostWithUrlEncodedFormData(GoodRequest):

        def topic(self):
            data = {'message':'Hello UrlEncoded Form'}
            return (200, data, self.post('/', data=data))

        def the_response_should_be_the_input(self, topic):
            _, data, response = topic
            expect(response.body).to_equal(json.dumps(data))
        
    class WhenPostWithMultipartFormData(WhenPostWithUrlEncodedFormData):

        def topic(self):
            data = {'message':'Hello Multipart Form'}
            return (200, data, self.post('/', data=data, multipart=True))
    
    class WhenPostWithFileUpload(GoodRequest):

        def topic(self):
            data = {'upload': ('the_file_name', 
                'This is the file content!')}
            return (200, data, self.post('/', data=data, multipart=True))

        def the_response_should_contain_upload(self, topic):
            _, _, response = topic
            body = json.loads(response.body)
            expect(body).to_include('upload')

        def the_response_should_contain_filename(self, topic):
            _, _, response = topic
            body = json.loads(response.body)['upload']
            expect(body).to_include('filename')

        def the_filename_should_be_the_same(self, topic):
            _, _, response = topic
            body = json.loads(response.body)['upload']
            expect(body['filename']).to_include('the_file_name')

        def the_file_should_have_the_same_content(self, topic):
            _, _, response = topic
            body = json.loads(response.body)['upload']['body']
            expect(body).to_equal('This is the file content!')

    class WhenPostWithMultipleFiles(WhenPostWithFileUpload):

        def topic(self):
            data = {'upload': 
                    ('the_file_name', 'This is the file content!'),
                    'second_file': ('other_file_name', 'Different content')
                    }
            return (200, data, self.post('/', data=data, multipart=True))
        
        def the_response_should_contain_second_file(self, topic):
            _, _, response = topic
            body = json.loads(response.body)
            expect(body).to_include('second_file')

        def the_response_should_contain_filename(self, topic):
            _, _, response = topic
            body = json.loads(response.body)['second_file']
            expect(body).to_include('filename')

        def the_second_filename_should_be_the_same(self, topic):
            _, _, response = topic
            body = json.loads(response.body)['second_file']
            expect(body['filename']).to_include('other_file_name')

        def the_content_of_the_second_file_should_be_the_same(self, topic):
            _, _, response = topic
            body = json.loads(response.body)['second_file']['body']
            expect(body).to_equal('Different content')

    class WhenPostWithFileUploadAndArguments(WhenPostWithFileUpload):

        def topic(self):
            data = {'upload': 
                    ('the_file_name', 'This is the file content!'),
                    'argument':'value'
                    }
            return (200, data, self.post('/', data=data, multipart=True))
        
        def the_response_should_contain_argument(self, topic):
            _, _, response = topic
            body = json.loads(response.body)
            expect(body).to_include('argument')

        def the_argument_should_have_value(self, topic):
            _, _, response = topic
            argument = json.loads(response.body)['argument']
            expect(argument).to_equal('value')


