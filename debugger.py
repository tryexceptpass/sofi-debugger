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

def trace_lines(frame, event, arg):
    """Handler that executes with every line of code"""

    # We only care about *line* and *return* events
    if event != 'line' and event != 'return':
        return

    # Get a reference to the code object and source
    co = frame.f_code
    source = inspect.getsourcelines(co)[0]

    # Send the UI information on the code we're currently executing
    trace_lines.applicationq.put({ "co": { "file": co.co_filename,
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

    # Wait for a debug command
    cmd = trace_lines.debugq.get()

    if cmd == "step":
        # If stepping through code, return this handler
        return trace_lines

    if cmd == "stop":
        # If stopping execution, raise an exception
        raise StopExecution()

    elif cmd == 'over':
        # If stepping out of code, return the function callback
        return trace_calls

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
    """Custom exception for stopping code execution"""

    pass

def trace_calls(frame, event, arg):
    """Handler that executes on every invocation of a function call"""

    # We only care about function call events
    if event != 'call':
        return

    # Get a reference for the code object and function name
    co = frame.f_code
    func_name = co.co_name

    # Only react to the functions we care about
    if func_name in ['sample', 'xyz']:
        # Get the source code from the code object
        source = inspect.getsourcelines(co)[0]

        # Tell the UI to perform an update
        trace_lines.applicationq.put({ "co": { "file": co.co_filename,
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

        # Wait for a debug command (we stop here right before stepping into or out of a function)
        cmd = trace_lines.debugq.get()

        if cmd == 'step':
            # If stepping into the function, return the line callback
            return trace_lines
        elif cmd == 'over':
            # If stepping over, then return nothing
            return

    return

def sample(a, b):
    """The sample function we'll be executing"""
    x = a + b
    y = x * 2
    print('Sample: ' + str(y))

def xyz(a):
    """Another sample function"""

    print("XYZ:" + str(a))

@asyncio.coroutine
def main(event):
    """Main UI initialization code that generates the base HTML for the web application"""

    # Create the view and container that will parent our widgets
    v = View()
    c = Container()

    # Create a row with a little spacing from the top
    r = Row(style="padding-top:20px;")

    # Make the toolbar that will contain the Step Into / Next, Stop and Step Over / Out buttons
    tb = ButtonToolbar(cl="pull-right", style="margin-top:-7px;")
    tb.addelement(Button("Next", ident="code-next-button"))
    tb.addelement(Button("Stop", ident="code-stop-button"))
    tb.addelement(Button("Step Over", ident="code-over-button"))

    # Create the span that will contain the short description of where we're at in code execution
    title = Span("", ident="code-panel-title")

    # Add the panel with the previous title and space for showing the code
    p = Panel(heading=True, ident="code")
    p.setheading(str(title) + str(tb))
    p.addelement(Paragraph())

    # Make a large 8-wide Bootstrap column to house our panel
    col = Column('lg', 8)

    # Add the panel to the column, to the row, to the container and view
    col.addelement(p)
    r.addelement(col)
    c.addelement(r)
    v.addelement(c)

    # Load the HTML generated from this widget structure onto the browser
    app.load(str(v))

@asyncio.coroutine
def load(event):
    """Load event handler. Runs where the base HTML from the main function completes loading"""

    # Start the background debug process
    debugprocess.start()

    # Register event handlers for the UI buttons
    app.register('click', step, selector="#code-next-button")
    app.register('click', stop, selector="#code-stop-button")
    app.register('click', over, selector="#code-over-button")

    # Start listening for display updates
    yield from display()

@asyncio.coroutine
def display():
    """Coroutine for updating the UI"""

    # Wait for the application queue to have an update to the display
    while True:
        if applicationq.empty():
            yield from asyncio.sleep(0.5)
        else:
            # The application queue has at least one item, let's act on every item that's in it
            while not applicationq.empty():
                # Get info on what we want to draw
                draw = applicationq.get()

                if 'trace' in draw:
                    # We're updating the type of trace, meaning the button names need to change

                    if draw['trace'] == 'call':
                        # We're outside of a function, so we want Step Into and Step Over
                        app.text("#code-next-button", "Step Into")
                        app.text("#code-over-button", "Step Over")
                    else:
                        # We're inside a function so we want Next and Step Out
                        app.text("#code-next-button", "Next")
                        app.text("#code-over-button", "Step Out")

                if "co" in draw:
                    # We have an update to the code object, so update the title of the panel widget to show the line and function we're on
                    app.replace("#code-panel-title", str(Sample(str(draw['co']['file']) + " - " +
                                                     draw['co']['name'] +
                                                     "() #" + str(draw['co']['lineno']))))
                if "frame" in draw:
                    # We have an update to the frame. so show the source code (nicely formatted) and point to the line we're on
                    app.replace("#code-panel-body", str(Sample(str(draw['frame']['locals'])))  +
                                                    str(formatsource(draw['frame'])))
            return

def formatsource(frame):
    """Format the source code provided with this frame an HTML representation"""

    # Iterate through the source code and made <div><samp></samp></div> sections for each line
    for index, item  in enumerate(frame['source']):
        d = Div()

        # If the line is indented, add some margin
        if item[0:1] == '\t' or item[0:1] == ' ':
            d.style ='margin-left:15px;'

        # If this is the line we're currently on, add a red marker to it
        if index == frame['lineno'] - frame['firstlineno']:
            d.addelement(Bold('> ', style="color:red"))

        # Update the source to show the HTML representation of what we just made
        d.addelement(Sample(item.replace("\n", "")))
        frame['source'][index] = str(d)

    return "".join(frame['source'])

@asyncio.coroutine
def step(event):
    """Click handler for the Step Into button"""

    # Tell the debugger we want to step in
    debugq.put("step")

    # Make sure we're updating the display
    yield from display()

@asyncio.coroutine
def stop(event):
    """Click handler for the Stop button"""

    # Tell the debugger we're stopping execution
    debugq.put("stop")

@asyncio.coroutine
def over(event):
    """Click handler for the Step Over / Step Out button"""

    # Tell the debugger to step over the next code block
    debugq.put("over")

def debug(applicationq, debugq, fn, args):
    """Sets up and starts the debugger"""

    # Setup the debug and application queues as properties of the trace_lines functions
    trace_lines.debugq = debugq
    trace_lines.applicationq = applicationq

    # Enable debugging by setting the callback
    sys.settrace(trace_calls)

    # Execute the function we want to debug with its parameters
    fn(*args)

if __name__ == '__main__':
    # Create a sofi-based application
    app = Sofi()

    # Register the initialization handler that will send the base HTML to the browser
    app.register('init', main)

    # Register a load event that will kick off our debugger
    app.register('load', load)

    # Initialize the debug and application queues for passing messages
    debugq = multiprocessing.Queue()
    applicationq = multiprocessing.Queue()

    # Create the debug process
    debugprocess = multiprocessing.Process(target=debug, args=(applicationq, debugq, sample, (2, 3)))

    # Start the application UI event server
    app.start()
