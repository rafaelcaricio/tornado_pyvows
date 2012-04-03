#!/usr/bin/env python
# -*- coding: utf-8 -*-

# tornado-pyvows extensions
# https://github.com/rafaelcaricio/tornado-pyvows

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 Rafael Caricio rafael@caricio.com
import json

from tornado_pyvows import TornadoHTTPContext
from pyvows import Vows, expect

REQUESTBIN_BASE_URL = 'http://requestb.in'

@Vows.batch
class Post(TornadoHTTPContext):

    def topic(self):
        response = self.post('%s/api/v1/bins' % REQUESTBIN_BASE_URL)
        requestbin_id = json.loads(response.body)['name']
        return (requestbin_id, response)

    def should_be_ok(self, topic):
        _, response = topic
        expect(response.code).to_equal(200)

    class Get(TornadoHTTPContext):

        def topic(self, post_response):
            requestbin_id, response = post_response
            get_response = self.get(
                    '%s/%s' % (REQUESTBIN_BASE_URL, requestbin_id))
            return get_response
        
        def should_be_ok(self, topic):
            expect(topic.code).to_equal(200)

    class Delete(TornadoHTTPContext):

        def topic(self, post_response):
            requestbin_id, response = post_response
            delete_response = self.delete(
                    '%s/%s' % (REQUESTBIN_BASE_URL, requestbin_id))
            return delete_response

        def should_be_ok(self, topic):
            expect(topic.code).to_equal(200)

    class Head(TornadoHTTPContext):

        def topic(self, post_response):
            requestbin_id, response = post_response
            head_response = self.head(
                    '%s/%s' % (REQUESTBIN_BASE_URL, requestbin_id))
            return head_response

        def should_be_ok(self, topic):
            expect(topic.code).to_equal(200)

    class Put(TornadoHTTPContext):

        def topic(self, post_response):
            requestbin_id, response = post_response
            put_response = self.put(
                    '%s/%s' % (REQUESTBIN_BASE_URL, requestbin_id), body='')
            return put_response

        def should_be_ok(self, topic):
            expect(topic.code).to_equal(200)
