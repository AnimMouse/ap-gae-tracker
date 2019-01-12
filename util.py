#!/usr/bin/python2.4

"""Utility methods.

Contains utility methods used by multiple modules.
"""

__author__ = 'allen@thebends.org (Allen Porter)'

import cgi
import os

def GetParam(name):
  params = cgi.parse_qs(os.environ['QUERY_STRING'])
  if params.has_key(name):
    return params[name][0]
  else:
    return ""
