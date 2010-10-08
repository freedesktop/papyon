# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2007 Ali Sabil <asabil@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from papyon.msnp.message import MessageAcknowledgement
from papyon.msnp2p.transport.TLP import MessageChunk
from papyon.msnp2p.transport.base import BaseP2PTransport
from papyon.switchboard_manager import SwitchboardHandler

import gobject
import struct
import logging

__all__ = ['SwitchboardP2PTransport']

logger = logging.getLogger('papyon.msnp2p.transport.switchboard')


class SwitchboardP2PTransport(BaseP2PTransport, SwitchboardHandler):

    MAX_OUTSTANDING_SENDS = 5

    def __init__(self, client, contacts, peer, peer_guid, transport_manager):
        self._oustanding_sends = 0
        self._peer = peer
        self._peer_guid = peer_guid
        SwitchboardHandler.__init__(self, client, contacts)
        BaseP2PTransport.__init__(self, transport_manager, "switchboard")

    def close(self):
        BaseP2PTransport.close(self)
        self._leave()

    @staticmethod
    def _can_handle_message(message, self=None):
        if self and (self.peer != message.sender or
                self.peer_guid != message.sender_guid):
            return False
        content_type = message.content_type[0]
        return content_type == 'application/x-msnmsgrp2p'

    @staticmethod
    def handle_peer(client, peer, peer_guid, transport_manager):
        return SwitchboardP2PTransport(client, (peer,), peer, peer_guid,
            transport_manager)

    @staticmethod
    def handle_message(client, message, transport_manager):
        peer = message.sender
        guid = message.sender_guid
        return SwitchboardP2PTransport(client, (), peer, guid,
            transport_manager)

    @property
    def peer(self):
        return self._peer

    @property
    def peer_guid(self):
        return self._peer_guid

    @property
    def rating(self):
        return 0

    @property
    def max_chunk_size(self):
        return 1250 # length of the chunk including the header but not the footer

    def can_send(self, peer, peer_guid, blob, bootstrap=False):
        return (self._peer == peer and self._peer_guid == peer_guid)

    def _ready_to_send(self):
        return (self._oustanding_sends < self.MAX_OUTSTANDING_SENDS)

    def _send_chunk(self, peer, peer_guid, chunk):
        logger.debug(">>> %s" % repr(chunk))
        if chunk.version is 1 or peer_guid is None:
            headers = {'P2P-Dest': self.peer.account}
        elif chunk.version is 2:
            headers = {'P2P-Src' : self._client.profile.account + ";{" +
                                   self._client.machine_guid + "}",
                       'P2P-Dest': peer.account + ";{" +
                                   peer_guid + "}"}
        content_type = 'application/x-msnmsgrp2p'
        body = str(chunk) + struct.pack('>L', chunk.application_id)
        self._oustanding_sends += 1
        self._send_message(content_type, body, headers,
                MessageAcknowledgement.MSNC,
                (self._on_message_sent, peer, peer_guid, chunk),
                (self._on_message_error, peer, peer_guid, chunk))

    def _on_message_received(self, message):
        version = 1
        peer = message.sender
        peer_guid = message.sender_guid
        dest_guid = message.parse_guid('P2P-Dest')
        # if destination contains a GUID, the protocol should be TLPv2
        if dest_guid and peer_guid:
            version = 2
            if dest_guid != self._client.machine_guid or \
               peer_guid != self._peer_guid:
                return # this chunk is not for us

        chunk = MessageChunk.parse(version, message.body[:-4])
        chunk.application_id = struct.unpack('>L', message.body[-4:])[0]
        logger.debug("<<< %s" % repr(chunk))
        self._on_chunk_received(peer, peer_guid, chunk)

    def _on_message_sent(self, peer, peer_guid, chunk):
        self._oustanding_sends -= 1
        self._on_chunk_sent(peer, peer_guid, chunk)

    def _on_message_error(self, peer, peer_guid, chunk):
        self._oustanding_sends -= 1

    def _on_switchboard_closed(self):
        pass

    def _on_closed(self):
        BaseP2PTransport.close(self)

    def _on_error(self, error_type, error):
        logger.info("Received error %i (type=%i)" % (error, error_type))

    def _on_contact_joined(self, contact):
        pass

    def _on_contact_left(self, contact):
        if contact == self._peer:
            self.close()

    def __repr__(self):
        return '<SwitchboardP2PTransport peer="%s" guid="%s">' % \
                (self.peer.account, self.peer_guid)
