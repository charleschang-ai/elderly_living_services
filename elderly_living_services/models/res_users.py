# -*- coding: utf-8 -*-
import requests
import base64
from odoo import models, api, fields
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def fetch_remote_file_proxy(self, url):
        try:
            response = requests.get(url)
            if response.status_code != 200:
                return {'error': 'Failed to fetch file from remote server'}

            file_name = url.split('/')[-1].split('?')[0] or 'downloaded_file'

            return {
                'content': base64.b64encode(response.content).decode('utf-8'),
                'mimetype': response.headers.get('Content-Type'),
                'name': file_name
            }
        except Exception as e:
            return {'error': str(e)}
