# -*- coding: utf-8 -*-

import os
import time
from tempfile import NamedTemporaryFile
from requests.exceptions import SSLError

import requests
import xmltodict
from dicttoxml import dicttoxml


BASE_URL        = 'https://pilot.mvoucher.se/ta/servlet/TA_XML'
CURRENT_PATH    = os.path.dirname(os.path.realpath(__file__))
CERTIFICATE     = '/'.join([CURRENT_PATH, 'data/rchery_butik.pem'])

ACTIONS = {}
ACTIONS['GET_PROVIDERS'] = {'TA_ACTION': '5-45102'}
ACTIONS['ISSUE'] = {'TA_ACTION': '5-45103'}


class Provider(object):

    def __init__(self, body):
        """ Populate an Provider instance base on body data. """
        for k, v in body.iteritems():
            self.__setattr__(k.replace('@','').lower(), v)

    def __repr__(self):
        """ Printable representation. """
        return ' - '.join([self.name, self.id])


class Retain24Wrapper(object):
    """
    Usage::

    >>> from retain24wrapper import Retain24Wrapper
    >>> r = Retain24Wrapper(url[optional])
    >>> providers = r.get_providers()
    [H&M - 001, Lindex - 002, ICA - 003]
    >>> r.issue_valuable(args)
    OrderedDict([(u'MSISDN', u'00467311122233'), ... (u'STATUS', u'OK')])

    """
    def __init__(self, url=BASE_URL, certificate=CERTIFICATE_PATH):
        """ Setup the retain wrapper object. """
        self.url = url
        self.certificate_path = CERTIFICATE_PATH
        self.providers = []

    def get_providers(self):
        """ Cet currently available providers.

            :return: self.providers: A list with available providers.
        """
        try:
            resp = requests.get(self.url, params=ACTIONS['GET_PROVIDERS'], cert=CERTIFICATE, verify=True, stream=True)
        except SSLError:
            print 'SSL handshake failed./n'
            return False

        content = xmltodict.parse(resp.content)

        for template in content['TICKETANYWHERE']['COUPON']['RESPONSE']['TEMPLATELIST']['TEMPLATE']:
            self.providers.append(Provider(template))

        return self.providers

    def populate_xml(self, template_id, qty, msisdn, **kwargs):
        """ Basically parse user-args to xml
        that is accepted by retin24 to issue a valuable/coupon.

        :param template_id: The retain24 id for a clinet/organization
        :param qty: The value of coupon 100 = 1 SEK
        :param msisdn: Customer id also customers phone number.

        :param: email_address: (optional) Customers email.
        :param: sms_text: (optional) SMS text.
        :param: email_text: (optional) Email text.
        :param: send_date: (optional) Date sent.

        :return: file: Valid xml file.
        """
        email_address = kwargs.get('email_address', 'None')
        sms_text = kwargs.get('sms_text', 'None')
        email_text = kwargs.get('email_text', 'None')
        send_date = kwargs.get('send_date', time.strftime('%Y-%m-%d %H:%m'))

        obj = {
            "COUPON": {
                "SEND": {
                    "TEMPLATE": template_id,
                    "QTY": qty,
                    "MSISDN": msisdn,
                    "EMAIL_ADDRESS": email_address,
                    "SMS_TEXT": sms_text,
                    "EMAIL_TEXT": email_text,
                    "SEND_DATE": send_date,
                }
            }
        }

        tmp = NamedTemporaryFile(mode='w+b', suffix='xml', delete=True)
        tmp.write(dicttoxml(obj, custom_root="TICKETANYWHERE", attr_type=False))
        tmp.seek(0)
        file = tmp.read()
        tmp.close()
        return file

    def parse_response(self, resp):
        """ Parse the issue and send response and checks for errors."""
        content = xmltodict.parse(resp.content)
        receipt = content['TICKETANYWHERE']['COUPON']['RESPONSE']['RECEIPT']

        if (receipt['STATUS'] == 'ERROR'):
            raise ValueError('ERRORCODE: {error_code} - {message}'.format(
                error_code=receipt['ERRORCODE'],
                message=receipt['MESSAGE']
            ))
        return receipt

    def issue_valuable(self, template_id, qty, msisdn, **kwargs):
        """ Generate a coupon (aka valuable).

        :param template_id: The retain24 id for a clinet/organization
        :param qty: The value of coupon 100 = 1 SEK
        :param msisdn: Customer id also customers phone number.

        :return receipt: Receipt or False
         """
        xml = self.populate_xml(template_id=template_id, qty=qty, msisdn=msisdn, **kwargs)
        try:
            resp = requests.post(
                self.url,
                data=xml,
                params=ACTIONS['ISSUE'],
                cert=CERTIFICATE,
                verify=True,
                stream=True
            )
        except SSLError:
            print 'SSL handshake failed./n'
            return False

        receipt = self.parse_response(resp)

        return receipt

print 'Running!'


