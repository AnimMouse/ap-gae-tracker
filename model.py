#!/usr/bin/python2.4

"""Data model.
"""

__author__ = 'allen@thebends.org (Allen Porter)'

import base64
from google.appengine.ext import db

class Torrent(db.Model):
  # Base64 encoded "info_hash" argument uniquely identifying the torrent
  info_hash = db.StringProperty(required=True)

  # Total number of times the tracker has registered a completion
  downloaded = db.IntegerProperty()

class TorrentPeerEntry(db.Model):
  # Base64 encoded "info_hash" argument identifying the torrent
  torrent = db.Reference(Torrent)

  # IP:port of the client
  ip = db.StringProperty(required=True)
  port = db.IntegerProperty(required=True)

  # Client supplied identifier
  peer_id = db.StringProperty(required=True)

  # Total amount downloaded (probably bytes)
  downloaded = db.IntegerProperty()

  # Total amount uploaded (probably bytes)
  uploaded = db.IntegerProperty()

  # Last time we saw the client
  last_datetime = db.DateTimeProperty(required=True)
