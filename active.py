#!/usr/bin/python2.4

"""One-line documentation for helloworld module.

A detailed description of helloworld.
"""

__author__ = 'allen@thebends.org (Allen Porter)'

import base64
import datetime
import os
import wsgiref.handlers

from google.appengine.ext import db
from google.appengine.ext import webapp
from BTL import bencode

import model

class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'

    cutoff_time = datetime.datetime.now() - datetime.timedelta(seconds=180)
    self.response.out.write("Active clients: (%s)\n" % cutoff_time)
    entries = model.TorrentPeerEntry.gql(
        "WHERE last_datetime >= :1 "
        "ORDER BY last_datetime DESC",
        cutoff_time)
    for entry in entries:
      self.response.out.write("%s %s (%s:%d) %s\n" % (entry.peer_id,
                              entry.torrent.info_hash, entry.ip, entry.port,
                              entry.last_datetime))

application = webapp.WSGIApplication(
    [ ( '/', MainPage ) ],
    debug=True)

# Hack so that we don't try to parse the info_hash as a UTF-8 string
#os.environ['CONTENT_TYPE'] = "%s;charset=" % os.environ['CONTENT_TYPE']
wsgiref.handlers.CGIHandler().run(application)
