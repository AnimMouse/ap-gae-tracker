#i!/usr/bin/python2.4

"""Announce module
"""

__author__ = 'allen@thebends.org (Allen Porter)'

import base64
import datetime
import os
import wsgiref.handlers
import cgi
import logging

from google.appengine.ext import db
from google.appengine.ext import webapp
from BTL import bencode

import model
import util

def compact_peer_info(ip, port):
  try:
    s = ( ''.join([chr(int(i)) for i in ip.split('.')])
          + chr((port & 0xFF00) >> 8) + chr(port & 0xFF) )
    if len(s) != 6:
      s = ''
  except:
    s = ''  # not a valid IP, must be a domain name
  return s

class MainPage(webapp.RequestHandler):
  def __init__(self):
    self._compact = False
    self._peers = None

  def get(self):
    info_hash = util.GetParam('info_hash')
    if len(info_hash) != 20:
      self.error("Invalid info_hash argument (%d != 20)" % (len(info_hash)))
      return
    peer_id = self.request.get('peer_id')
    if len(peer_id) != 20:
      self.error("Invalid peer_id argument")
      return
    ip = os.environ['REMOTE_ADDR']
    # TODO(aporter): Get the optional ip from the client (for proxies)
    try:
      port = int(self.request.get('port'))
    except ValueError: 
      self.error("Invalid port argument")
      return
    try:
      uploaded = int(self.request.get('uploaded'))
    except ValueError: 
      self.error("Invalid uploaded argument")
      return
    try:
      downloaded = int(self.request.get('downloaded'))
    except ValueError: 
      self.error("Invalid downloaded argument")
      return
    try:
      left = int(self.request.get('left'))
    except ValueError: 
      self.error("Invalid left argument")
      return
    try:
      compact = int(self.request.get('compact'))
    except ValueError: 
      self.error("Invalid compact argument")
      return
    try:
      numwant = int(self.request.get('numwant'))
    except ValueError: 
      self.error("Invalid numwant argument")
      return
    if compact != 0 and compact != 1:
      self.error("Invalid corrupt argument")
      return
    self._compact = (compact == 1)
    no_peer_id = not compact

    # TODO(aporter): Event handling
    event = self.request.get('event', None)

    # TODO(aporter): Used to prove identity to tracker if ip changes
    key = self.request.get('key')

    torrents = model.Torrent.gql("WHERE info_hash = :1",
                                 base64.b64encode(info_hash))
    if torrents.count() == 1:
      torrent = torrents[0]
    else:
      torrent = model.Torrent(info_hash=base64.b64encode(info_hash))
    torrent.put()

    peers = model.TorrentPeerEntry.gql(
        "WHERE torrent = :1 AND peer_id = :2 AND ip = :3 AND port = :4",
        torrent, peer_id, ip, port)
    if peers.count() == 1:
      peer = peers[0]
      # TODO(aporter): Should we reject peers with differing IP and port or
      # should they be allowed to update? This depends on if this peer id can
      # be guessed by others or not.
      peer.ip = ip
      peer.port = port
      peer.last_datetime = datetime.datetime.now()
    else:
      peer = model.TorrentPeerEntry(torrent=torrent,
                                    ip=ip,
                                    port=port,
                                    peer_id=peer_id,
                                    last_datetime=datetime.datetime.now())
    peer.downloaded = downloaded
    peer.uploaded = uploaded
    peer.put()

    self.BuildPeersResult(torrent, peer_id)
    self.CleanupOldPeers(torrent)

    # TOOD(aporter): Respect maximum number of peers
    num_complete = 1
    num_incomplete = 0

    self.response.headers['Content-Type'] = 'text/plain'
    result = {
        "interval" : 60,
        "complete" : num_complete,
        "incomplete" : num_incomplete,
        "peers" : self._peers
      }
    self.response.out.write(bencode.bencode(result))

  def error(self, msg):
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write(bencode.bencode({ "failure reason" : msg }))

  def BuildPeersResult(self, torrent, current_peer_id):
    cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes = 3)
    peers = model.TorrentPeerEntry.gql("WHERE torrent = :1 AND " +
                                       "last_datetime >= :2",
                                       torrent, cutoff_time)
    if not self._compact:
      self._peers = [ ]
      for peer_entry in peers:
        if peer_entry.peer_id != current_peer_id:
          self._peers.append({
              "peer id" : str(peer_entry.peer_id),
              "ip" : str(peer_entry.ip),
              "port" : peer_entry.port,
            })
    else:
      self._peers = ""
      for peer_entry in peers:
        if peer_entry.peer_id != current_peer_id:
          self._peers += compact_peer_info(peer_entry.ip, peer_entry.port)

  def CleanupOldPeers(self, torrent):
    cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes = 10)
    query = db.GqlQuery("SELECT * FROM TorrentPeerEntry " +
                        "WHERE last_datetime < :1",
                        cutoff_time)
    results = query.fetch(10)  # Do some small cleanup
    if results:
      logging.info("Deleting %d torrent peer entries" % len(results))
      for result in results:
        result.delete()

application = webapp.WSGIApplication(
    [ ( '/announce', MainPage ) ],
    debug=True)

# Hack so that we don't try to parse the info_hash as a UTF-8 string
#os.environ['CONTENT_TYPE'] = "%s;charset=" % os.environ['CONTENT_TYPE']
wsgiref.handlers.CGIHandler().run(application)
