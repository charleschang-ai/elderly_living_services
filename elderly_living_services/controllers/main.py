from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
import pytz


class ElderlyWebsite(http.Controller):
    @http.route('/elderly_services', type='http', auth="public", website=True)
    def elderly_services_page(self, **kwargs):
        services = request.env['elderly.service'].sudo().search([('is_published', '=', True)])
        return request.render('elderly_living_services.elderly_service_template', {
            'services': services
        })

    @http.route('/service_pricing', type='http', auth="public", website=True)
    def elderly_pricing_page(self, **kwargs):
        services = request.env['elderly.service'].sudo().search([('is_published', '=', True)], order="category_id")
        return request.render('elderly_living_services.elderly_pricing_template2', {
            'services': services
        })

    @http.route('/elderly_appointment', type='http', auth="user", website=True)
    def appointment_form(self, **kwargs):
        if not request.session.uid:
            return request.redirect('/web/login', 303)

        target_service_id = int(kwargs.get('service_id', 0))

        services = request.env['elderly.service'].sudo().search([('is_published', '=', True)])

        last_booking = request.env['elderly.appointment'].sudo().search(
            [('user_id', '=', request.env.user.id), ('state', '=', 'draft')], order='create_date desc', limit=1
        )
        user_tz = pytz.timezone(request.env.user.tz or 'Asia/Hong_Kong')

        now_utc = datetime.now(pytz.utc)
        now_local = now_utc.astimezone(user_tz)

        default_start = now_local.strftime('%Y-%m-%dT%H:%M')
        default_end = (now_local + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M')

        values = {
            'services': services,
            'target_service_id': target_service_id,
            'last_booking': last_booking,
            'user': request.env.user,
            'default_start': default_start,
            'default_end': default_end,
        }
        return request.render('elderly_living_services.appointment_submit_template', values)

    @http.route('/elderly_appointment/submit', type='http', auth="user", methods=['POST'], website=True, csrf=False)
    def submit_appointment(self, **post):
        user_tz = pytz.timezone(request.env.user.tz or 'Asia/Hong_Kong')

        def convert_to_utc(date_str):
            if not date_str:
                return False
            dt = datetime.strptime(date_str.replace('T', ' '), '%Y-%m-%d %H:%M')
            local_dt = user_tz.localize(dt)
            return local_dt.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')

        # 創建預約紀錄
        booking_vals = {
            'service_id': int(post.get('service_id')),
            'contact_name': post.get('contact_name'),
            'email': post.get('email'),
            'phone': post.get('phone'),
            'start_time': convert_to_utc(post.get('start_time')),
            'end_time': convert_to_utc(post.get('end_time')),
            'note': post.get('note'),
            'state': 'submitted',  # 直接提交
            'user_id': request.env.user.id,
        }
        new_booking = request.env['elderly.appointment'].sudo().create(booking_vals)

        # 提交後跳轉到成功頁面或首頁
        return request.render('elderly_living_services.booking_success_template', {'booking': new_booking})

    @http.route('/my/elderly_appointments', type='http', auth="user", website=True)
    def my_appointments(self, **kwargs):
        if not request.session.uid:
            return request.redirect('/web/login', 303)

        # 獲取當前用戶的所有預約記錄，按創建時間倒序
        appointments = request.env['elderly.appointment'].sudo().search(
            [('user_id', '=', request.env.user.id), ('state', '!=', 'draft')], order='create_date desc'
        )
        return request.render('elderly_living_services.my_appointments_template', {
            'appointments': appointments,
        })
