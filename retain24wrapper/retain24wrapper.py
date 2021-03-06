# -*- coding: utf-8 -*-

import time
from tempfile import NamedTemporaryFile
from xml.etree import cElementTree as ET
from xml.etree.cElementTree import XML

from dicttoxml import dicttoxml
import requests
import xmltodict


ACTIONS = {}
ACTIONS['GET_PROVIDERS'] = {'TA_ACTION': '5-45103'}
ACTIONS['ISSUE'] = {'TA_ACTION': '5-45102'}
ACTIONS['VALIDATE'] = {'TA_ACTION': '5-43101'}

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
    >>> r = Retain24Wrapper(base_url, certificate_path)
    >>> providers = r.get_providers()
    [H&M - 001, Lindex - 002, ICA - 003]
    >>> r.issue_valuable(args)
    OrderedDict([(u'MSISDN', u'00467311122233'), ... (u'STATUS', u'OK')])
    >>> r.validate_valuable(args)
    OrderedDict([(u'CPNINFO'...

    """
    def __init__(self, base_url, certificate_path):
        """ Setup the retain wrapper object. """
        self.base_url = base_url
        self.certificate_path = certificate_path
        self.providers = []

    def parse_response(self, resp):
        """Parse response data into a dictionary."""
        return xmltodict.parse(resp.content)['TICKETANYWHERE']['COUPON']['RESPONSE']

    def populate_xml(self, body, **kwargs):
        """ Prepare the xml data to be sent to the api"""
        tmp = NamedTemporaryFile(mode='w+b', suffix='xml', delete=True)

        root = ET.Element("TICKETANYWHERE")
        coupon = ET.SubElement(root, "COUPON", {'VER': '1.0'})

        body_xml = XML(dicttoxml(body, root=False, attr_type=False))
        if (kwargs.get('body_attrs')):
            body_xml.attrib = kwargs.get('body_attrs')

        coupon.append(body_xml)
        tmp.write('<?xml version="1.0" encoding="ISO-8859-1" ?>')
        ET.ElementTree(root).write(tmp)

        tmp.seek(0)
        file = tmp.read()
        tmp.close()

        return file

    def validate_receipt(self, resp):
        """ Parse the issue and send response and checks for errors."""
        receipt = self.parse_response(resp)['RECEIPT']

        if (receipt['STATUS'] == 'ERROR'):
            raise ValueError('ERRORCODE: {error_code} - {message}'.format(
                error_code=receipt['ERRORCODE'],
                message=receipt['MESSAGE']
            ))
        return receipt

    def get_providers(self):
        """ Cet currently available providers.

            :return: self.providers: A list with available providers.
        """

        resp = requests.get(self.base_url, params=ACTIONS['GET_PROVIDERS'], cert=self.certificate_path, verify=True, stream=True)

        for template in self.parse_response(resp)['TEMPLATELIST']['TEMPLATE']:
            self.providers.append(Provider(template))

        return self.providers

    def issue_valuable(self, template_id, qty, msisdn, **kwargs):
        """ Generate a coupon (aka valuable).

        :param template_id: The retain24 id for a clinet/organization
        :param qty: The value of coupon 100 = 1 SEK
        :param msisdn: Customer id also customers phone number.

        :param: email_address: (optional) Customers email.
        :param: sms_text: (optional) SMS text.
        :param: email_text: (optional) Email text.
        :param: send_date: (optional) Date sent.

        :return receipt: Receipt
         """
        email_address = kwargs.get('email_address', 'None')
        sms_text = kwargs.get('sms_text', 'None')
        email_text = kwargs.get('email_text', 'None')
        send_date = kwargs.get('send_date', time.strftime('%Y-%m-%d %H:%m'))

        obj = {
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

        xml = self.populate_xml(obj)

        resp = requests.post(
            self.base_url,
            data=xml,
            params=ACTIONS['ISSUE'],
            cert=self.certificate_path,
            verify=True,
            stream=True
        )

        receipt = self.validate_receipt(resp)

        return receipt

    def validate_valuable(self, msisdn, pin, multicode):
        """ Valudate a valuable aka. coupon.

        :param multicode: The unique code for a valuable.
        :param pin: Pincode, set to empty string if provider doesnt need it.
        :param msisdn: Customer id also customers phone number.
        """
        obj = {
            "VALIDATE": {
                "MSISDN": msisdn,
                "PIN": pin,
                "MULTICODE": multicode
            }
        }

        xml = self.populate_xml(body=obj, body_attrs={'TYPE': 'STANDARD'})

        resp = requests.post(
            self.base_url,
            data=xml,
            params=ACTIONS['VALIDATE'],
            cert=self.certificate_path,
            verify=True,
            stream=True
        )

        return self.parse_response(resp)
