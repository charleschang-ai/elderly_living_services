# -*- coding: utf-8 -*-
################################################################################
#    Author: Charles
#
################################################################################
{
    'name': 'Elderly Living Services',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """To ensure that every senior citizen enjoys a dignified, convenient, and fulfilling later life.""",
    'description': """To ensure that every senior citizen enjoys a dignified, convenient, and fulfilling later life.""",
    'author': 'Robert Lee',
    'maintainer': 'Charles',
    'depends': ['web', 'base', 'sale', 'website', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/main_template.xml',
        'data/fee_list.xml',
        'data/make_appointment.xml',
        'data/sequence_data.xml',
        'data/my_order.xml',
        'views/elder_service_menuitem.xml',
        'views/elder_service.xml',
        'views/appointment_form.xml',
    ],
    # 'assets': {
    #     # 'web.assets_backend': [
    #     #     'file_scanning_sava/static/src/js/**/*',
    #     #     'file_scanning_sava/static/src/xml**/*',
    #     # ],
    #     'web.assets_frontend': [
    #         'file_scanning_sava/static/src/js/**/*',
    #         'file_scanning_sava/static/src/xml/**/*',
    #     ],
    # },
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 50,
    'currency': "USD",
}
