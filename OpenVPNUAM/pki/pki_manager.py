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

"""PKI - Public Key Infrastructure program class

This class is in charge of management of all certificates operations
renewal and also their revocation.
This is the entry point of all SSL operations
"""

# System imports
import logging
import os
import datetime

try:
  import OpenSSL
  from OpenSSL import crypto
  from OpenSSL import SSL
  #OpenSSL.crypto._lib.OPENSSL_config(b"openssl.cn")
except ImportError:
  raise Exception("Module OpenSSL required " +
                  " https://pypi.python.org/pypi/pyOpenSSL")

# Project imports
from .pki_filetree import PKIFileTree
from .. import models as Model
from ..config import Error

# Global project declarations
g_sys_log = logging.getLogger('openvpn-uam.pki')


class PublicKeyInfrastructure(object):
  """Build an instance of the pki model class

  This instance must be called in the openvpn uam program class
  """

  def __init__(self, confparser):
    """Constructor : Build a new PKI API instance
    """
    self.__cp = confparser
    # the file tree to use to store all file
    self.__ft = PKIFileTree(confparser)
    # path to CA cert
    self.__certificate_authority = None
    # path to CA key
    # needed to certify new certificates for hostnames
    self.__certificate_authority_key = None
    # Path to the server certificate, use to ensure that this certificate is
    # still valid
    self.__server_certificate = None
    # number of bits for new private key
    self.__cert_key_size = int(2048)

  def load(self):
    """Return a boolean indicates if PKI is ready to work or not

    This function check things required by PKI working and return a boolean
    that indicates if the PKI is ready to work with certificate or not
    @return [bool] The ready status
    """
    g_sys_log.info("Using %s",
                   SSL.SSLeay_version(SSL.SSLEAY_VERSION).decode())
    # check PKI section in configuration file
    if not self.__cp.has_section(self.__cp.PKI_SECTION):
      g_sys_log.fatal('Missing pki section in configuration file')
      return False
    if not self.__ft.load():
      g_sys_log.fatal('Enabled to load File Manager for PKI')
      return False

    self.__cert_key_size = self.__cp.getint(
        self.__cp.PKI_SECTION,
        'cert_key_size',
        fallback=self.__cert_key_size)

    try:
      self.__certificate_authority = self.loadCertificate(
          self.__cp.get(
              self.__cp.PKI_SECTION,
              'ca'))
      self.__certificate_authority_key = self.loadPrivateKey(
          self.__cp.get(
              self.__cp.PKI_SECTION,
              'ca_key'))
    except Error as e:
      g_sys_log.error('Configuration error : ' + str(e))
      return False
    if self.__certificate_authority is None:
      g_sys_log.error('CA Certificate is missing')
      return False
    else:
      g_sys_log.info("Using CA Certificate '%s'",
                     self.__certificate_authority.get_subject().CN)
    if self.__certificate_authority_key is None:
      g_sys_log.error('CA Key is missing')
      return False
    else:
      g_sys_log.info("Using CA Private Key with size '%s' bits",
                     self.__certificate_authority_key.bits())
    return True

  def checkRequirements(self):
    """Check requirement for PKI to running

    @return [bool] : True if all requirement are valid
                    False ifone of them are not valid
    """
    if self.__certificate_authority.has_expired():
      g_sys_log.error('CA Certificate has expired')
      return False
    if not self.__certificate_authority_key.check():
      g_sys_log.error('CA Private Key is invalid')
      return False
    return True

# TOOLS
  def loadCertificate(self, path):
    """Import an existing certificate from file to python object

    @param path [str] : the path to the certificate file to import
    @return [OpenSSL.crypto.X509] the certificate object that correspond to the
                                  certificate file
            [None] if an error occur
    """
    assert path is not None
    try:
      # open file in binary mode
      f_cert = open(path, 'rb').read()
    except IOError as e:
      g_sys_log.error('Unable to open certificate file : ' + str(e))
      return None

    lib_crypto = OpenSSL.crypto
    try:
      # try to load the cert as PEM format
      cert = lib_crypto.load_certificate(lib_crypto.FILETYPE_PEM, f_cert)
    except lib_crypto.Error as e:
      # if error try with another format
      try:
        # try to load the cert as ASN1 format
        cert = lib_crypto.load_certificate(lib_crypto.FILETYPE_ASN1, f_cert)
        g_sys_log.warning('Certificate "%s" is not in PEM recommanded format',
                          path)
      except lib_crypto.Error as e:
        g_sys_log.error('Unable to import certificate : ' + str(e))
        return None
    return cert

  def loadPrivateKey(self, path):
    """Import an private key from file to python object

    @param path [str] : the path to the private key file to import
    @return [OpenSSL.crypto.PKey] the certificate object that correspond to the
                                  certificate file
            [None] if an error occur
    """
    assert path is not None
    try:
      # open file in binary mode
      f_cert = open(path, 'rb').read()
    except IOError as e:
      g_sys_log.error('Unable to open private key file : ' + str(e))
      return None

    lib_crypto = OpenSSL.crypto
    try:
      # try to load the key as PEM format
      key = lib_crypto.load_privatekey(lib_crypto.FILETYPE_PEM, f_cert)
    except lib_crypto.Error as e:
      # if error try with another format
      try:
        # try to load the cert as ASN1 format
        key = lib_crypto.load_privatekey(lib_crypto.FILETYPE_ASN1, f_cert)
        g_sys_log.warning('Private Key "%s" is not in PEM recommanded format',
                          path)
      except lib_crypto.Error as e:
        g_sys_log.error('Unable to import private key : ' + str(e))
        return None
    return key

  def generateUserCertificate(self, user, hostname):
    """
    """
    g_sys_log.debug("Building a new certificate for Hostname(%s) '%s'",
                    hostname.id, hostname.name)

    # build a new key for the given username
    g_sys_log.debug("Generate a %s bits RSA Private Key", self.__cert_key_size)
    key = OpenSSL.crypto.PKey()
    key.generate_key(OpenSSL.crypto.TYPE_RSA, self.__cert_key_size)

    g_sys_log.debug("Generate a X509 certificate")
    cert = OpenSSL.crypto.X509()
    cert.get_subject().C = self.__certificate_authority.get_subject().C
    cert.get_subject().ST = self.__certificate_authority.get_subject().ST
    cert.get_subject().L = self.__certificate_authority.get_subject().L
    cert.get_subject().O = self.__certificate_authority.get_subject().O
    cert.get_subject().OU = self.__certificate_authority.get_subject().OU
    cert.get_subject().CN = user.cuid + "_" + hostname.name
    cert.get_subject().emailAddress = user.user_mail
    cert.get_subject().name = (user.cuid + "_" + hostname.name + "_" +
                               str(datetime.datetime.today()))

    cert.set_notBefore(b"20000101000000Z")
    cert.set_notAfter(b"20200101000000Z")

    cert.set_serial_number(0)
    cert.set_issuer(self.__certificate_authority.get_subject())
    cert.set_pubkey(key)
    #cert.sign(cakey, "sha1")

    m_cert = Model.Certificate(cert.get_notBefore(), cert.get_notAfter())
    
    self.__ft.storePKIUserCertificate(user, hostname, m_cert, key)
    self.__ft.storePKIUserCertificate(user, hostname, m_cert, cert)