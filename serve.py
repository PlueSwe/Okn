#!/usr/bin/env python3
"""Liten statisk server för den fristående appen. Kör: python3 serve.py"""
import os, functools
from http.server import HTTPServer, SimpleHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
Handler = functools.partial(SimpleHTTPRequestHandler, directory=HERE)
HTTPServer(("127.0.0.1", 8123), Handler).serve_forever()
