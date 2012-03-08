#!/usr/bin/env python
# -*- coding: utf-8 -*-

# tornado-pyvows extensions
# https://github.com/rafaelcaricio/tornado-pyvows

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 Daniel Truemper truemped@googlemail.com
from functools import partial

from pyvows import Vows, expect
from tornado_pyvows import TornadoContext


def async_method(callback):
    callback("Pseudo Async Result")

@Vows.batch
class AsyncVows(TornadoContext):

    class CallbacksShouldWork(TornadoContext):

        def topic(self):
            self.io_loop = self.get_new_ioloop()
            self.io_loop.add_callback(partial(async_method, self.stop))
            return self.wait()

        def and_have_the_correct_result(self, topic):
            expect(topic).to_equal("Pseudo Async Result")
