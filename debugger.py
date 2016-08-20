from sofi.app import Sofi
from sofi import Container, View, Row, Column, Span, Div, Panel
from sofi import Bold, Sample, Paragraph, ButtonToolbar, Button

import asyncio
import json
import time

from datetime import datetime

import inspect
import sys

import multiprocessing

# Tue Jun 07 23:05:55 +0000 2016
dateformat = "%a %b %d %H:%M:%S %z %Y"

def trace_lines(frame, event, arg):
    if event != 'line':
        return

    co = frame.f_code

    source = inspect.getsourcelines(co)[0]
    for index, item  in enumerate(source):
        d = Div()

        if item[0:1] == '\t' or item[0:1] == ' ':
            d.style ='margin-left:15px;'

        if index == frame.f_lineno - co.co_firstlineno:
            d.addelement(Bold('>', style="color:red"))

        d.addelement(Sample(item.replace("\n", "")))
        source[index] = str(d)

    source = "".join(source)

    print("CODE")
    print("co_argcount " + str(co.co_argcount))
    print("co_cellvars " + str(co.co_cellvars))
    print("co_code " + str(co.co_code))
    print("co_consts " + str(co.co_consts))
    print("co_filename " + str(co.co_filename))
    print("co_firstlineno " + str(co.co_firstlineno))
    print("co_flags " + str(co.co_flags))
    print("co_freevars " + str(co.co_freevars))
    print("co_kwonlyargcount " + str(co.co_kwonlyargcount))
    print("co_lnotab " + str(co.co_lnotab))
    print("co_name " + str(co.co_name))
    print("co_names " + str(co.co_names))
    print("co_nlocals " + str(co.co_nlocals))
    print("co_stacksize " + str(co.co_stacksize))
    print("co_varnames " + str(co.co_varnames))

    print("FRAME")
    print("clear " + str(frame.clear))
    # print("f_back " + str(frame.f_back))
    # print("f_builtins " + str(frame.f_builtins))
    # print("f_code " + str(frame.f_code))
    print("f_globals " + str(frame.f_globals))
    print("f_lasti " + str(frame.f_lasti))
    print("f_lineno " + str(frame.f_lineno))
    print("f_locals " + str(frame.f_locals))
    print("f_trace " + str(frame.f_trace))


    trace_lines.dbgq.get()

    trace_lines.appq.put({'name': 'replace',
                          'html': str(Sample(str(co.co_filename) + " - " + co.co_name + "() #" + str(frame.f_lineno))),
                          'selector': '#code-panel-title'})
    trace_lines.appq.put({'name': 'replace',
                          'html': str(Sample(str(frame.f_locals)))  + str(source),
                          'selector': '#code-panel-body'})



def trace_calls(frame, event, arg):
    if event != 'call':
        return

    co = frame.f_code
    func_name = co.co_name

    if func_name == 'abc':
        print('Call to %s on line %s of %s' % (func_name, frame.f_lineno, co.co_filename))
        return trace_lines

    return

def abc(x):
    x = x + 1
    y = x * 2
    print("ABC: " + str(x + y))


@asyncio.coroutine
def main(event, interface):
    print("MAIN")
    v = View()
    c = Container()
    r = Row()

    tb = ButtonToolbar(cl="pull-right")
    tb.addelement(Button("Next", ident="code-next-button"))

    title = Span("", ident="code-panel-title")

    p = Panel(heading=True, ident="code")
    p.setheading(str(title) + str(tb))
    p.addelement(Paragraph())

    col = Column('lg', 8)
    col.addelement(p)
    r.addelement(col)

    c.addelement(r)
    v.addelement(c)

    return { 'name': 'init', 'html': str(v) }

@asyncio.coroutine
def load(event, interface):
    print("LOADED")

    p.start()

    app.register('click', step, selector="#code-next-button")


@asyncio.coroutine
def display(event, interface):
    while True:
        if appq.empty():
            print("APP: waiting")
            yield from asyncio.sleep(1)
        else:
            print("APP: dispatching")
            while not appq.empty():
                interface.dispatch(appq.get())
            return

@asyncio.coroutine
def step(event, interface):
    print("STEP")
    dbgq.put(1)
    yield from display(event, interface)

def debug(appq, dbgq, fn, args):
    trace_lines.dbgq = dbgq
    trace_lines.appq = appq
    sys.settrace(trace_calls)
    fn(args)

if __name__ == '__main__':
    dbgq = multiprocessing.Queue()
    appq = multiprocessing.Queue()

    app = Sofi()
    app.register('init', main)
    app.register('load', load)

    p = multiprocessing.Process(target=debug, args=(appq, dbgq, abc, (23)))
    app.start()
