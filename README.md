# Retain 24 Wrapper
Wrapper for the Retain 24 web services. Currently only support get providers and issue a valueable.

## Installation
The wrapper need a certificate file.

Usage::

    >>> from retain24wrapper import Retain24Wrapper
    >>> r = Retain24Wrapper(url[optional])
    >>> providers = r.get_providers()
    [H&M - 001, Lindex - 002, ICA - 003]
    
    >>> r.issue_valuable(args)
    OrderedDict([(u'MSISDN', u'00467311122233'), ... (u'STATUS', u'OK')])
    
## Generate certificate

    $ python setup.py
    $ openssl pkcs12 -in cert.pfx -out cert.pem -nodes
    
 Put the generated file in /certificates folder