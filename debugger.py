from sofi.app import Sofi
from sofi.ui import Container, View, Row, Column, Span, Div, Panel
from sofi.ui import Bold, Sample, Paragraph, ButtonToolbar, Button

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
    print("TRACE_LINES")
    if event != 'line' and event != 'return':
        return

    co = frame.f_code
    source = inspect.getsourcelines(co)[0]

    trace_lines.appq.put({ "co": { "file": co.co_filename,
                                   "name": co.co_name,
                                   "lineno": str(frame.f_lineno)
                                   },
                          "frame": { "lineno": frame.f_lineno,
                                      "firstlineno": co.co_firstlineno,
                                      "locals": str(frame.f_locals),
                                      "source": source
                                      },
                           'trace': 'line'
                          })

    cmd = trace_lines.dbgq.get()
    if cmd == "step":
        return trace_lines
    if cmd == "stop":
        raise StopExecution()
    elif cmd == 'over':
        return 

    # print("CODE")
    # print("co_argcount " + str(co.co_argcount))
    # print("co_cellvars " + str(co.co_cellvars))
    # print("co_code " + str(co.co_code))
    # print("co_consts " + str(co.co_consts))
    # print("co_filename " + str(co.co_filename))
    # print("co_firstlineno " + str(co.co_firstlineno))
    # print("co_flags " + str(co.co_flags))
    # print("co_freevars " + str(co.co_freevars))
    # print("co_kwonlyargcount " + str(co.co_kwonlyargcount))
    # print("co_lnotab " + str(co.co_lnotab))
    # print("co_name " + str(co.co_name))
    # print("co_names " + str(co.co_names))
    # print("co_nlocals " + str(co.co_nlocals))
    # print("co_stacksize " + str(co.co_stacksize))
    # print("co_varnames " + str(co.co_varnames))
    #
    # print("FRAME")
    # print("clear " + str(frame.clear))
    # # print("f_back " + str(frame.f_back))
    # # print("f_builtins " + str(frame.f_builtins))
    # # print("f_code " + str(frame.f_code))
    # # print("f_globals " + str(frame.f_globals))
    # print("f_lasti " + str(frame.f_lasti))
    # print("f_lineno " + str(frame.f_lineno))
    # print("f_locals " + str(frame.f_locals))
    # print("f_trace " + str(frame.f_trace))

class StopExecution(Exception):
    pass

def trace_calls(frame, event, arg):
    if event != 'call':
        return

    co = frame.f_code
    func_name = co.co_name

    # Here is where we should control major debug flow
    print("FUNCTION CALL", func_name)
    if func_name == 'abc':
        source = inspect.getsourcelines(co)[0]

        trace_lines.appq.put({ "co": { "file": co.co_filename,
                                       "name": co.co_name,
                                       "lineno": str(frame.f_lineno)
                                       },
                              "frame": { "lineno": frame.f_lineno,
                                          "firstlineno": co.co_firstlineno,
                                          "locals": str(frame.f_locals),
                                          "source": source
                                          },
                              "trace": "call"
                              })

        print('Call to %s on line %s of %s' % (func_name, frame.f_lineno, co.co_filename))

        cmd = trace_lines.dbgq.get()

        if cmd == 'step':
            try:
                return trace_lines
            except StopExecution:
                pass
        elif cmd == 'over':
            return

    return

def abc(x):
    x = x + 1
    y = x * 2
    print("ABC: " + str(x + y))


@asyncio.coroutine
def main(event):
    print("MAIN")
    v = View()
    c = Container()
    r = Row()

    tb = ButtonToolbar(cl="pull-right")
    tb.addelement(Button("Next", ident="code-next-button"))
    tb.addelement(Button("Stop", ident="code-stop-button"))
    tb.addelement(Button("Step Over", ident="code-over-button"))

    title = Span("", ident="code-panel-title")

    p = Panel(heading=True, ident="code")
    p.setheading(str(title) + str(tb))
    p.addelement(Paragraph())

    col = Column('lg', 8)
    col.addelement(p)
    r.addelement(col)

    c.addelement(r)
    v.addelement(c)

    app.load(str(v))

@asyncio.coroutine
def load(event):
    p.start()

    app.register('click', step, selector="#code-next-button")
    app.register('click', stop, selector="#code-stop-button")
    app.register('click', over, selector="#code-over-button")

    yield from display()

@asyncio.coroutine
def display():
    while True:
        if appq.empty():
            yield from asyncio.sleep(1)
        else:
            while not appq.empty():
                draw = appq.get()
                if 'trace' in draw:
                    if draw['trace'] == 'call':
                        app.text("#code-next-button", "Step Into")
                        app.text("#code-over-button", "Step Over")
                    else:
                        app.text("#code-next-button", "Next")
                        app.text("#code-over-button", "Step Out")

                if "co" in draw:
                    app.replace("#code-panel-title", str(Sample(str(draw['co']['file']) + " - " +
                                                     draw['co']['name'] +
                                                     "() #" + str(draw['co']['lineno']))))
                if "frame" in draw:
                    app.replace("#code-panel-body", str(Sample(str(draw['frame']['locals'])))  +
                                                    str(formatsource(draw['frame'])))
            return

def formatsource(frame):
    for index, item  in enumerate(frame['source']):
        d = Div()

        if item[0:1] == '\t' or item[0:1] == ' ':
            d.style ='margin-left:15px;'

        if index == frame['lineno'] - frame['firstlineno']:
            d.addelement(Bold('>', style="color:red"))

        d.addelement(Sample(item.replace("\n", "")))
        frame['source'][index] = str(d)

    return "".join(frame['source'])

@asyncio.coroutine
def step(event):
    dbgq.put("step")
    yield from display()

@asyncio.coroutine
def stop(event):
    dbgq.put("stop")

@asyncio.coroutine
def over(event):
    dbgq.put("over")

def debug(appq, dbgq, fn, args):
    trace_lines.dbgq = dbgq
    trace_lines.appq = appq
    sys.settrace(trace_calls)
    fn(args)

if __name__ == '__main__':

    app = Sofi()
    app.register('init', main)
    app.register('load', load)

    dbgq = multiprocessing.Queue()
    appq = multiprocessing.Queue()
    p = multiprocessing.Process(target=debug, args=(appq, dbgq, abc, (23)))
    app.start()
