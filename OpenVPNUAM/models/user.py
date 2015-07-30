# -*- coding: utf8 -*-

# This file is a part of OpenVPN-UAM
#
# Copyright (c) 2015 Thomas PAJON, Pierre GINDRAUD
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Models/User

This file contains the class of Users entities
"""

# System imports
import datetime
import logging

# Project imports
from .hostname import Hostname
from ..helpers import *

# Global project declarations
g_sys_log = logging.getLogger('openvpn-uam.model.user')


class User(object):
  """Build an instance of the user program class
  """

  def __init__(self, cuid, mail):
    """Constructor: Build a new empty user

    @param cuid [str] : common unique user identifier
    @param mail [str] : main mail address of this user
    """
    # database model
    self._id = None
    self._cuid = cuid
    self._user_mail = mail
    self._certificate_mail = None
    self._password_mail = None
    self._is_enabled = False
    self._certificate_password = None
    self._start_time = None
    self._stop_time = None
    self._creation_time = datetime.datetime.today()
    self._update_time = None
    # python model
    self.__lst_hostname = []

  def load(self, attributs, hostnames):
    """Load an user entity with attributs

    @param attributs [dict] : a key-value dict which contains attributs
    to set to this User object
    """
    # already set
    assert self._id is None
    if self._id is not None:
      return

    # load attributes
    assert isinstance(attributs, dict)
    # loop for each given attributes
    for key in attributs:
      if hasattr(self, "_" + key):
        setattr(self, "_" + key, attributs[key])
      else:
        g_sys_log.error('Unknown attribute from source "' + key + '"')

    # load hostnames
    assert isinstance(hostnames, list)
    self.__lst_hostname = hostnames

# Getters methods
  def getHostnameList(self):
    """Get the list of the user's hostname

    @return [list] : list of hostnames used by the user
    """
    return self.__lst_hostname

  def getId(self):
    """Return the current User ID

    @return [int] the id
    """
    if self._id is None:
      return None
    try:
      return int(self._id)
    except ValueError as e:
      g_sys_log.error('Error with User ID format ' + str(type(self._id)))
      helper_log_fatal(g_sys_log, 'error_models.user.fatal')

# Setters methods
  def setId(self, id):
    """Set the current user's ID

    If the id is already set, do nothing
    @param id [int] : the new id
    """
    # ASSERT
    assert self._id is None

    if self._id is not None:
      return
    try:
      self._id = int(id)
    except ValueError as e:
      g_sys_log.error('Error with User ID format ' + str(type(self._id)))
      helper_log_fatal(g_sys_log, 'error_models.user.fatal')

  def addHostname(self, hostname):
    """addHostname(): Add an hostname to the user

    @param hostname [Hostname] : an hostname will be used by the user
    """
    if isinstance(hostname, Hostname):
      print("TODO INTERNAL ERROR")
      return
    self.__lst_hostname.append(hostname)
    """ --Add the entry in the Database-- """

  def enable(self):
    """enable(): Change the state of the user to enabled
    """
    if self._is_enable is True:
      print("TODO INTERNAL ERROR")
      return
    self._is_enable = True

  def disable(self):
    """disable(): Change the state of the user to disabled
    """
    if self._is_enable is False:
      print("TODO INTERNAL ERROR")
      return
    self._is_enable = False

  def __str__(self):
    """[DEBUG] Produce a description string for this user instance

    @return [str] a formatted string that describe this user
    """
    content = ("USER (" + str(self._id) + ")" +
               "\n  CUID = " + str(self._cuid) +
               "\n  UMAIL = " + str(self._user_mail) +
               "\n  CERTMAIL = " + str(self._certificate_mail) +
               "\n  PASSMAIL = " + str(self._password_mail) +
               "\n  STATUS = " + str(self._is_enabled) +
               "\n  CERT PASSWD = " + str(self._certificate_password) +
               "\n  START DATE = " + str(self._start_time) +
               "\n  END DATE = " + str(self._stop_time) +
               "\n  CREATED ON = " + str(self._creation_time) +
               "\n  UPDATED ON = " + str(self._update_time))
    for h in self.__lst_hostname:
      content += "\n" + str(h)
    return content

  def __repr__(self):
    """[DEBUG] Produce a list of attribute as string for this user instance

    @return [str] a formatted string that describe this user
    """
    return ("[id(" + str(self._id) + ")," +
            " cuid(" + str(self._cuid) + ")," +
            " umail(" + str(self._user_mail) + ")," +
            " certmail(" + str(self._certificate_mail) + ")," +
            " passmail(" + str(self._password_mail) + ")," +
            " enable(" + str(self._is_enabled) + ")," +
            " certpasswd(" + str(self._certificate_password) + ")," +
            " startdate(" + str(self._start_time) + ")," +
            " enddate(" + str(self._stop_time) + ")," +
            " createdon(" + str(self._creation_time) + ")," +
            " updatedon(" + str(self._update_time) + ")," +
            " hostname(" + str(len(self.__lst_hostname)) + ")]")
