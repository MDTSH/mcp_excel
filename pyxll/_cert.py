"""
Copyright (c) 2021, All Rights Reserved, http://www.pyxll.com/

THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY
KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
PARTICULAR PURPOSE.
"""
from ._errors import Help, Error
from ._utils import _check_excel_is_not_running
import logging
import ctypes
import ctypes.wintypes
import sys
import os

_log = logging.getLogger(__name__)

_cert_file = "pyxll.crt"

if sys.version_info[:2] >= (3, 9):
    import importlib.resources
    def _resource_bytes(package, resource_name):
        ref = importlib.resources.files(package).joinpath(resource_name)
        with ref.open('rb') as fp:
            return fp.read()

if sys.version_info[:2] >= (3, 7):
    import importlib.resources
    def _resource_bytes(package, resource_name):
        return importlib.resources.read_binary(package, resource_name)

else:
    import pkg_resources
    def _resource_bytes(package, resource_name):
        return pkg_resources.resource_stream(package, resource_name).read()

def _install_certificate(*args):
    """Installs a trusted publisher certificate for the current user."""
    unexpected_args = args
    if unexpected_args:
        raise Help("Unexpected arguments '%s' to command 'uninstall'." % ", ".join(unexpected_args))

    _check_excel_is_not_running()

    # Load the crt (PEM) file
    path = os.path.join(os.path.dirname(__file__), _cert_file)
    if os.path.exists(path):
        data = open(path, "rb").read()
    else:
        data = _resource_bytes("pyxll", _cert_file)

    crypt32 = ctypes.WinDLL("crypt32.dll", use_last_error=True)

    HCERTSTORE = ctypes.c_void_p
    PCCERT_CONTEXT = ctypes.c_void_p
    PBYTE = ctypes.POINTER(ctypes.wintypes.BYTE)  # wintypes.PBYTE not in all Python versions
    PDWORD = ctypes.POINTER(ctypes.wintypes.DWORD)

    CryptStringToBinaryW = crypt32.CryptStringToBinaryW
    CryptStringToBinaryW.argtypes = (
        ctypes.wintypes.LPWSTR,  # pszString
        ctypes.wintypes.DWORD,  # cchString
        ctypes.wintypes.DWORD,  # dwFlags
        PBYTE,  # pbBinary
        PDWORD,  # pcbBinary
        PDWORD,  # pdwSkip
        PDWORD  # pdwFlags
    )
    CryptStringToBinaryW.restypes = ctypes.wintypes.BOOL

    wdata = ctypes.create_unicode_buffer(data.decode())
    encoded_size = ctypes.wintypes.DWORD(0)
    if not CryptStringToBinaryW(wdata,
                                len(wdata),
                                0,  # CRYPT_STRING_BASE64HEADER
                                None,
                                ctypes.byref(encoded_size),
                                None,
                                None):
        raise Error("Unable to read certificate file '%s' (%d)." % (_cert_file, ctypes.get_last_error()))

    if encoded_size == 0:
        raise Error("Error reading certificate file '%s' (%d)." % (_cert_file, ctypes.get_last_error()))

    encoded_buffer = (ctypes.wintypes.BYTE * encoded_size.value)()
    if not CryptStringToBinaryW(wdata,
                                len(wdata),
                                0,  # CRYPT_STRING_BASE64HEADER
                                encoded_buffer,
                                ctypes.byref(encoded_size),
                                None,
                                None):
        raise Error("Error reading certificate file '%s' (%d)." % (_cert_file, ctypes.get_last_error()))

    CertCreateCertificateContext = crypt32.CertCreateCertificateContext
    CertCreateCertificateContext.argtypes = (
        ctypes.wintypes.DWORD,  # dwCertEncodingType
        PBYTE,  # pbCertEncoded
        ctypes.wintypes.DWORD  # cbCertEncoded
    )
    CertCreateCertificateContext.restype = PCCERT_CONTEXT

    CertFreeCertificateContext = crypt32.CertFreeCertificateContext
    CertFreeCertificateContext.argtypes = PCCERT_CONTEXT,

    context = CertCreateCertificateContext(0x1,  # X509_ASN_ENCODING
                                           encoded_buffer,
                                           encoded_size)

    if not context:
        raise Error("Error creating certificate context: %d" % ctypes.get_last_error())

    CertAddCertificateContextToStore = crypt32.CertAddCertificateContextToStore
    CertAddCertificateContextToStore.argtypes = (
        HCERTSTORE,  # hCertStore
        PCCERT_CONTEXT,  # pCertContext
        ctypes.wintypes.DWORD,  # dwAddDisposition
        ctypes.POINTER(PCCERT_CONTEXT)  # ppStoreContext
    )
    CertAddCertificateContextToStore.restype = ctypes.wintypes.BOOL

    CertOpenSystemStoreW = crypt32.CertOpenSystemStoreW
    CertOpenSystemStoreW.argtypes = (ctypes.c_void_p, ctypes.wintypes.LPCWSTR)
    CertOpenSystemStoreW.restype = HCERTSTORE

    CertCloseStore = crypt32.CertCloseStore
    CertCloseStore.argtypes = (HCERTSTORE, ctypes.wintypes.DWORD)
    CertCloseStore.restype = ctypes.c_bool

    try:
        cert_store = CertOpenSystemStoreW(None, ctypes.c_wchar_p("TrustedPublisher"))
        if not cert_store:
            raise Error("Error opening TrustedPublisher certificate store: %d" % ctypes.get_last_error())

        try:
            if not CertAddCertificateContextToStore(cert_store,
                                                    context,
                                                    6,  # CERT_STORE_ADD_NEWER
                                                    None):
                error = ctypes.get_last_error()
                if error == -2146885627:  # CRYPT_E_EXISTS
                    _log.debug("Certificate is already installed")
                    return True
                raise Error("Error adding certificate: %d" % ctypes.get_last_error())

            _log.debug("Certificate added to Trusted Publishers certificate store.")
            return True
        finally:
            CertCloseStore(cert_store, 0)
    finally:
        CertFreeCertificateContext(context)