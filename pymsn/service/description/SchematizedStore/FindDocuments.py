# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

from common import *

def transport_headers():
    """Returns a dictionary, containing transport (http) headers
    to use for the request"""

    return {}

def soap_action():
    """Returns the SOAPAction value to pass to the transport
    or None if no SOAPAction needs to be specified"""

    return "http://www.msn.com/webservices/storage/w10/FindDocument"

def soap_body(cid):
    """Returns the SOAP xml body
    """
    return """<FindDocuments xmlns="http://www.msn.com/webservices/storage/w10">
            <objectHandle>
                <RelationshipName>
                    /UserTiles
                </RelationshipName>
                <Alias>
                    <Name>
                        %(cid)s
                    </Name>
                    <NameSpace>
                        MyCidStuff
                    </NameSpace>
                </Alias>
            </objectHandle>
            <documentAttributes>
                <ResourceID>
                    true
                </ResourceID>
                <Name>
                    true
                </Name>
            </documentAttributes>
            <documentFilter>
                <FilterAttributes>
                    None
                </FilterAttributes>
            </documentFilter>
            <documentSort>
                <SortBy>
                    DateModified
                </SortBy>
            </documentSort>
            <findContext>
                <FindMethod>
                    Default
                </FindMethod>
                <ChunkSize>
                    25
                </ChunkSize>
            </findContext>
        </FindDocuments>""" % { 'cid' : cid,
                                'profile_rid' : profile_rid,
                                'p_date_modified' : p_date_modified,
                                'expression_rid' : expression_rid,
                                'e_date_modified' : e_date_modified,
                                'display_name' : display_name,
                                'dn_last_modified' : dn_last_modified,
                                'personal_status' : personal_status,
                                'ps_last_modified' : ps_last_modified,
                                'user_tile_url' : user_tile_url,
                                'photo' : photo,
                                'flags' : flags }

def process_response(soap_response):
    return None
