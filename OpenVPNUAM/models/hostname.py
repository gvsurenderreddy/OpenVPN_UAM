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

"""Models/Hostname

This file contains class for hostname.
It provide some function to manage this hostname and also to update
its attributes.
"""

# System imports
import datetime
from datetime import timedelta
import logging

# Project imports
from .certificate import Certificate

# Global project declarations
g_sys_log = logging.getLogger('openvpn-uam.model.hostname')


class Hostname(object):
  """Build an instance of the hostname program class
  """

  def __init__(self, name):
    """Constructor: Build a new empty hostname

    @param name [str] : the name of the hostname
    """
    # database model
    self._id = None
    self._name = name
    self._period_days = None
    self._is_enabled = False
    self._is_online = False
    self._creation_time = datetime.datetime.today()
    self._update_time = None
    # python model
    # This is the list of NOT YET AVAILABLE certificates
    # These certificates doesn't need to perform specific action on them
    self.__l_certificate_soon_valid = []
    # This is the list of VALID certificates
    # These certificates doesn't need to perform specific action on them
    self.__l_certificate_valid = []
    # This is the list of SOON EXPIRED certificates
    # If there is a certificates in this list it indicates that the program
    # must begin to perform a regen of new certificate to prevent VPN accesss
    # failure
    self.__l_certificate_soon_expired = []
    # This is the list of EXPIRED certificates
    # Certificates in this list are sentenced to be destroyed by python garbage
    # collector in the next DB update
    self.__l_certificate_expired = []
    # This is the reference to the main database class
    # it is used to perform self object update call
    # Exemple if you want to update a attribut of an instance of this class
    # like one of theses above, you will need to call the main database to
    # store change into database engine
    self.__db = None

  def load(self, attributs, certs=[]):
    """Load an hostname entity with attributs

    @param attributs [dict] : a key-value dict which contains attributs
    to set to this Hostname object
    """
    assert self._id is None
    assert isinstance(attributs, dict)
    # loop for each given attributes
    for key in attributs:
      if hasattr(self, "_" + key):
        setattr(self, "_" + key, attributs[key])
      else:
        g_sys_log.error('Unknown attribute from source "' + key + '"')
    # load certificates
    self.loadCertificate(certs)

  def loadCertificate(self, certs):
    """Import and sort certificates into this hostname

    This function load given certificates list and sort them into four category
    according to their living dates
    @param certs [list<Certificate>] the pool of available certificates
    """
    assert isinstance(certs, list)
    # set uniq local time reference
    cur_time = datetime.datetime.today()
    # sort each given certificates into exiting categories
    for cert in certs:
      assert isinstance(cert, Certificate)
      # SOON VALID
      if cur_time < cert.certificate_begin_time:
        self.__l_certificate_soon_valid.append(cert)
      # CURRENTLY VALID
      elif (cert.certificate_begin_time <= cur_time and
            cur_time <= cert.certificate_end_time):
        vd = cert.getValidityDuration()
        # sort certificates into differents category by their
        # validity duration
        d = 0
        h = 0
        m = 0
        # VD <= 6HOURS : 20minutes
        if vd <= timedelta(hours=6):
          m = 20
        # 6HOURS < VD <= 1DAY : 4hours
        elif timedelta(hours=6) < vd and vd <= timedelta(days=1):
          h = 4
        # 1DAY < VD <= 3DAYS : 1day
        elif timedelta(days=1) < vd and vd <= timedelta(days=3):
          d = 1
        # 3DAYS < VD <= 7DAYS : 2days
        elif timedelta(days=3) < vd and vd <= timedelta(days=7):
          d = 2
        # 7DAYS < VD : 4days
        else:
          d = 4
        # if current timedate is out of expiry anticipation bounds
        if cur_time < (cert.certificate_end_time -
                       timedelta(days=d, hours=h, minutes=m)):
          self.__l_certificate_valid.append(cert)
        else:
          self.__l_certificate_soon_expired.append(cert)
      # EXPIRED
      else:
        self.__l_certificate_expired.append(cert)

# Getters methods
  def __getattr__(self, key):
    """Upgrade default getter to allow get semi-private attributes
    """
    try:
      return object.__getattribute__(self, "_" + key)
    except AttributeError:
      pass
    return object.__getattribute__(self, key)

  @property
  def period_days(self):
    """Return the number of day to use for new certificate

    @return [int] the number of day new certificates will be certified for
    """
    if self._period_days <= 0:
      return 30
    return self._period_days

  @property
  def db(self):
    """Return the db instance associated with this user

    @return [Database] the database reference
    """
    assert self.__db is not None
    return self.__db

  def getCertificateValidList(self):
    """Return the list of valid certificate

    return [list<Certificate>]
    """
    return self.__l_certificate_valid

  def getCertificateSoonExpiredList(self):
    """Return the list of soon expired certificate

    return [list<Certificate>]
    """
    return self.__l_certificate_soon_expired

  def getCertificateValidCount(self):
    """Compute the total amount of certificate currently valid

    @return [int] the amount of currently valid certificate
          include VALID + SOON EXPIRED
    """
    return (len(self.__l_certificate_valid) +
            len(self.__l_certificate_soon_expired))

# Setters methods
  def __setattr__(self, key, value):
    """Upgrade default setter to trigger database update
    """
    # update concerns a Model's attribut
    if hasattr(self, "_" + key):
      setattr(self, "_" + key, value)
      self.db.update(key, value, self, 1)
    else:
      return object.__setattr__(self, key, value)

  @db.setter
  def db(self, db):
    """Set the internal DB link to allow self update

    Add reference to main database into this user and all his hostname
    @param db [Database] : the database instance to use for self update call
    """
    assert self.__db is None
    self.__db = db
    for h in self.__l_certificate_soon_valid:
      h.db = db
    for h in self.__l_certificate_valid:
      h.db = db
    for h in self.__l_certificate_soon_expired:
      h.db = db
    for h in self.__l_certificate_expired:
      h.db = db

# API methods
  def updateCertificateList(self):
    """Sort the list of certificate according to their expiry date

    This function mix all certificate into a single list and pass it to the
    loadCertificate() to be newly sorted by different categories
    """
    lst_all = []

    for h in self.__l_certificate_soon_valid:
      lst_all.append(h)
    self.__l_certificate_soon_valid = []

    for h in self.__l_certificate_valid:
      lst_all.append(h)
    self.__l_certificate_valid = []

    for h in self.__l_certificate_soon_expired:
      lst_all.append(h)
    self.__l_certificate_soon_expired = []

    # DON'T CARE ABOUT EXPIRED CERTIFICATE

    self.loadCertificate(lst_all)

  def addCertificate(self, cert):
    """Try to add the given certificate into the local storage

    @param cert [Certificate] the certificate to add
    @return [bool] True is add success, False otherwise
    """
    # check if the certificate have already been given to database
    if cert.id is None:
      cert.db = self.db
      if not self.db.insert(cert, self, True):
        return False

    # insert into local collection
    self.loadCertificate([cert])
    return True

# DEBUG methods
  def __str__(self):
    """[DEBUG] Produce a description string for this hostname instance

    @return [str] a formatted string that describe this hostname
    """
    content = ("  HOSTNAME (" + str(self._id) + ")" +
               "\n    NAME = " + str(self._name) +
               "\n    PERIOD (DAY) = " + str(self._period_days) +
               "\n    STATUS = " + str(self._is_enabled) +
               "\n    ONLINE STATUS = " + str(self._is_online) +
               "\n    CREATED ON = " + str(self._creation_time) +
               "\n    UPDATED ON = " + str(self._update_time))
    for c in self.__l_certificate_soon_valid:
      content += "\n  SV-" + str(c)
    for c in self.__l_certificate_valid:
      content += "\n   V-" + str(c)
    for c in self.__l_certificate_soon_expired:
      content += "\n  SE-" + str(c)
    for c in self.__l_certificate_expired:
      content += "\n   E-" + str(c)
    return content

  def __repr__(self):
    """[DEBUG] Produce a list of attribute as string for this hostname instance

    @return [str] a formatted string that describe this hostname
    """
    return ("[id({}), name({}), period({}), enable({})," +
            " createdon({}), updatedon({})," +
            " certificate-sv({}), certificate-v({})," +
            " certificate-se({}), certificate-e({})").format(
        str(self._id),
        str(self._name),
        str(self._period_days),
        str(self._is_enabled),
        str(self._creation_time),
        str(self._update_time),
        str(len(self.__l_certificate_soon_valid)),
        str(len(self.__l_certificate_valid)),
        str(len(self.__l_certificate_soon_expired)),
        str(len(self.__l_certificate_expired)))
