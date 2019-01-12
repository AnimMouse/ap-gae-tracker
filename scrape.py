#!/usr/bin/python2.4

"""One-line documentation for helloworld module.

A detailed description of helloworld.
"""

__author__ = 'allen@thebends.org (Allen Porter)'

import os
import base64
import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext import db

import model
import util
from BTL import bencode

class MainPage(webapp.RequestHandler):
  def __init__(self):
    self._files = { }

  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'
    info_hash = util.GetParam('info_hash')
    if len(info_hash) == 20:
      torrents = model.Torrent.gql("WHERE info_hash = :1",
                                base64.b64encode(info_hash))
    else:
      torrents = model.Torrent.gql("ORDER BY downloaded")
    for torrent in torrents:
      self.AddResult(torrent)
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write(bencode.bencode(self._files))

  def AddResult(self, torrent):
    self._files[base64.b64decode(torrent.info_hash)] = {
        'complete' : 0,     # of seeders
        'downloaded' : 0,   # 'event=complete' seen
        'incomplete' : 0,   # leechers
        # Optional 'name' in the .torrent
      }

application = webapp.WSGIApplication(
    [ ( '/scrape', MainPage ) ],
    debug=True)

#os.environ['CONTENT_TYPE'] = "%s;charset=utf8" % os.environ['CONTENT_TYPE']
wsgiref.handlers.CGIHandler().run(application)
