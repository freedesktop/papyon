# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2005-2007 Ali Sabil <ali.sabil@gmail.com>
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

"""Switchboard Manager
The switchboard manager is responsible for managing all the switchboards in
use, it simplifies the complexity of the switchboard crack."""

import logging
import gobject

import msnp
from transport import ServerType

__all__ = ['SwitchboardManager']

logger = logging.getLogger('protocol:switchboard_manager')

class SwitchboardClient(object):
    def __init__(self, client, contacts):
        self._client = client
        self._switchboard_manager = self._client._switchboard_manager
        self._switchboard = None
        self._switchboard_requested = False

        self._invite_queue = list(contacts)
        self._message_queue = []

        self._contacts = set()

        if len(self._invite_queue) > 0:
            self._switchboard_manager.request_switchboard(self)
            self._switchboard_requested = True

    @staticmethod
    def mime_types(self):
        return ("*",)



    def _send_message(self,
            content_type, body, ack=msnp.MessageAcknowledgement.HALF):
        if self._switchboard is None or \
                self._switchboard.state != msnp.ProtocolState.OPEN:
            self.__request_switchboard()
            self._message_queue.append((content_type, body, ack))
        else:
            self.__send_message(content_type, body, ack)

    def _invite_user(self, contact):
        if self._switchboard is None or \
                self._switchboard.state != msnp.ProtocolState.OPEN:
            self.__request_switchboard()
            self._invite_queue.append(contact)
        else:
            self._switchboard.invite_user(message)

    def _close(self):
        self._switchboard_manager.close_handler(self)

    def _on_message_received(self, message):
        pass

    def _on_message_sent(self, message):
        pass

    def _on_contact_joined(self, contact):
        pass

    def _on_contact_left(self, contact):
        pass

    def _on_error(self, switchboard, error_type, error):
        pass

    def _on_switchboard_update(self, switchboard):
        del self._switchboard
        self._switchboard = switchboard
        self._switchboard_requested = False
        self._contacts = set(self._switchboard.participants.values())
        if len(self._invite_queue) > 0:
            self.__process_invite_queue()
        else:
            self.__process_message_queue()
        self._switchboard.connect("user-joined",
                lambda sb, contact: self.__on_user_joined(contact))
        self._switchboard.connect("user-left",
                lambda sb, contact: self.__on_user_left(contact))
        self._switchboard.connect("user-invitation-failed",
                lambda sb, contact: self.__on_user_invitation_failed(contact))

    def __on_user_joined(self, contact):
        self._contacts.add(contact)
        if contact in self._invite_queue:
            self._invite_queue.remove(contact)
            if len(self._invite_queue) == 0:
                self.__process_message_queue()

        self._on_contact_joined(contact)

    def __on_user_left(self, contact):
        if len(self._contacts) > 1:
            self._contacts.remove(contact)
            self._on_contact_left(contact)

    def __on_user_invitation_failed(self, contact):
        if contact in self._invite_queue:
            self._invite_queue.remove(contact)
            if len(self._invite_queue) == 0:
                self.__process_message_queue()
    
    # Helper functions
    def __send_message(self, content_type, body, ack):
        trd_id = self._switchboard._transport.transaction_id
        message = msnp.OutgoingMessage(trd_id, ack)
        message.content_type = content_type
        message.body = body
        self._switchboard.send_message(message)

    def __request_switchboard(self):
        if not self._switchboard_requested:
            logger.info("requesting new switchboard")
            self._switchboard_manager.request_switchboard(self)
            self._invite_queue.extend(self._contacts)
            self._switchboard_requested = True

    def __process_invite_queue(self):
        for contact in self._invite_queue:
            self._switchboard.invite_user(contact)

    def __process_message_queue(self):
        for message_params in self._message_queue:
            self.__send_message(*message_params)
        self._message_queue = []


class SwitchboardManager(gobject.GObject):
    """Switchboard management
        
        @undocumented: do_get_property, do_set_property
        @group Handlers: _handle_*, _default_handler, _error_handler"""

    def __init__(self, client):
        """Initializer

            @param client: the main Client instance"""
        gobject.GObject.__init__(self)
        self._client = client
        self._handlers = set()
        self._switchboards = {}
        self._pending_switchboards = {}
        self._client._protocol.connect("switchboard-invitation-received",
                self.__ns_switchboard_invite)

    def request_switchboard(self, handler):
        self._client._protocol.\
                request_switchboard(self.__ns_request_response, handler)

    def close_handler(self, handler):
        pass

    def __ns_request_response(self, session, handler):
        sb = self.__build_switchboard(session)
        self._pending_switchboards[sb] = handler

    def __ns_switchboard_invite(self, session, inviter):
        self.__build_switchboard(session)

    def __build_switchboard(self, session):
        server, session_id, key = session
        transport_class = self._client._transport_class
        transport = transport_class(server, ServerType.SWITCHBOARD,
                self._client._proxies)
        sb = msnp.SwitchboardProtocol(self._client, transport,
                session_id, key, self._client._proxies)
        sb.connect("notify::state", self.__sb_state_change)
        transport.establish_connection()
        return sb

    def __sb_state_change(self, switchboard, param_spec):
        state = switchboard.state
        if state == msnp.ProtocolState.OPEN:
            self._switchboards[switchboard] = set()
            try:
                handler = self._pending_switchboards[switchboard]
                self._switchboards[switchboard].add(handler)
                del self._pending_switchboards[switchboard]
                handler._on_switchboard_update(switchboard)
            except:
                pass
        elif state == msnp.ProtocolState.CLOSED:
            del self._switchboards[switchboard]

    def __sb_message_received(self, switchboard, message):
        for handler in self._handlers:
            if handler._switchboard != switchboard:
                continue
            mime_types = handler.mime_types()
            if message.content_type[0] in mime_types or \
                    '*' in mime_types:
                handler._on_message_received(message)

