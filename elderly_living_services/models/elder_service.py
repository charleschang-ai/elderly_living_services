from markupsafe import Markup

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ElderlyServiceCategory(models.Model):
    _name = 'elderly.service.category'
    _description = '服務類別'

    name = fields.Char(string='類別名稱', required=True)
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(default=True)


class ElderlyService(models.Model):
    _name = 'elderly.service'
    _description = '養老服務主表'

    name = fields.Char(string='服務名稱', required=True)
    category_id = fields.Many2one('elderly.service.category', string='服務類別')
    description = fields.Html(string='服務描述')
    image = fields.Binary(string='服務圖片')

    price = fields.Float(string='參考價格')
    duration = fields.Float(string='預計時長(小時)')
    target_age = fields.Selection([
        ('all', '不限'),
        ('50', '50歲以上'),
        ('60', '60歲以上'),
        ('70', '70歲以上'),
        ('80', '80歲以上')
    ], string='適用年齡段', default='all')
    product_id = fields.Many2one(
        'product.product',
        string='對應銷售產品',
        required=True,
        help="此服務在銷售訂單中對應的產品項目"
    )
    is_published = fields.Boolean(
        string='是否發佈',
        default=False,
        help="勾選後，該服務即可在預約系統中被選取"
    )
    unit_name = fields.Char(string='計費單位', default='次', translate=True)


class ElderlyAppointment(models.Model):
    _name = 'elderly.appointment'
    _description = '服務預約表'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='預約編號', readonly=True, copy=False, default=lambda self: _('New'))
    service_id = fields.Many2one('elderly.service', string='預約服務', required=True, tracking=True)
    product_id = fields.Many2one('product.product', related='service_id.product_id', string='服務產品', store=True,
                                 readonly=True)

    user_id = fields.Many2one('res.users', string='申請人', default=lambda self: self.env.user, tracking=True)
    contact_name = fields.Char(string='聯繫人姓名', required=True)
    email = fields.Char(string='電子郵箱')
    phone = fields.Char(string='聯繫電話', required=True)

    # appointment_date = fields.Datetime(string='預約時間', required=True, tracking=True)
    state = fields.Selection([
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('confirmed', '已確認'),
        ('sale', '已開單'),
        ('rejected', '已拒絕'),
        ('completed', '服務完成'),
        ('canceled', '已取消')
    ], string='服務狀態', default='draft', tracking=True)

    note = fields.Text(string='用戶需求備註')
    rejection_reason = fields.Text(string='拒絕/取消原因')

    start_time = fields.Datetime(string='服務開始時間', required=True, tracking=True)
    end_time = fields.Datetime(string='服務結束時間', required=True, tracking=True)

    duration = fields.Float(string='實際時長(小時)', compute='_compute_duration', store=True)

    sale_order_count = fields.Integer(string="銷售訂單數量", compute='_compute_sale_order_count')
    sale_order_ids = fields.One2many('sale.order', 'appointment_id', string='關聯銷售訂單')

    payment_status = fields.Selection([
        ('not_paid', '未支付'),
        ('partial', '部分支付'),
        ('paid', '已支付'),
        ('no_invoice', '無賬單')
    ], string='支付狀態', compute='_compute_payment_status', tracking=True, compute_sudo=True)

    @api.depends('sale_order_ids',
                 'sale_order_ids.invoice_ids',
                 'sale_order_ids.invoice_ids.payment_state',
                 'sale_order_ids.invoice_ids.state')
    def _compute_payment_status(self):
        for rec in self:

            invoices = self.env['account.move'].search([
                ('invoice_origin', 'in', rec.sale_order_ids.mapped('name')),
                ('state', '!=', 'cancel')
            ])

            if not invoices:
                rec.payment_status = 'no_invoice'
                continue
            states = invoices.mapped('payment_state')

            if all(s in ['paid', 'in_payment'] for s in states):
                rec.payment_status = 'paid'
            elif any(s in ['paid', 'in_payment', 'partial'] for s in states):
                rec.payment_status = 'partial'
            else:
                rec.payment_status = 'not_paid'

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                diff = rec.end_time - rec.start_time
                rec.duration = diff.total_seconds() / 3600.0
            else:
                rec.duration = 0.0

    @api.constrains('start_time', 'end_time')
    def _check_dates(self):
        for rec in self:
            if rec.start_time and rec.end_time and rec.start_time > rec.end_time:
                raise ValidationError(_("服務結束時間不能早於開始時間！"))

    def action_submit(self):
        self.state = 'submitted'

    def action_confirm(self):
        self.state = 'confirmed'

    def action_cancel(self):
        self.state = 'canceled'

    def action_create_sale_order(self):
        for rec in self:
            if not rec.user_id.partner_id:
                raise UserError(_("該申請人未關聯客戶(Partner)，請先在用戶設置中配置。"))

            order = self.env['sale.order'].create({
                'partner_id': rec.user_id.partner_id.id,
                'appointment_id': rec.id,
                'origin': rec.name,
                'order_line': [(0, 0, {
                    'product_id': rec.product_id.id,
                    'product_uom_qty': 1,
                    'price_unit': rec.service_id.price,
                    'name': rec.service_id.name,
                })],
            })

            rec.state = 'sale'

            body = Markup(_("已成功生成銷售訂單: <a href='/web#id=%s&model=sale.order&view_type=form'>%s</a>")) % (
                order.id, order.name)
            rec.message_post(body=body)

            rec._compute_payment_status()

            return {
                'name': _('銷售訂單'),
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'res_id': order.id,
                'view_mode': 'form',
                'target': 'current',
            }

    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = self.env['sale.order'].search_count([('origin', '=', rec.name)])

    def action_view_sales(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
        action['domain'] = [('origin', '=', self.name)]
        action['context'] = {'default_origin': self.name}
        return action

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('elderly.appointment') or _('New')
        return super().create(vals_list)

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id:
            self.contact_name = self.user_id.name
            self.email = self.user_id.email
            self.phone = self.user_id.phone

    def action_complete(self):
        """將狀態改為完成"""
        for rec in self:
            if rec.state != 'sale':
                pass
            rec.state = 'completed'
            rec.message_post(body="服務已圓滿完成。")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    appointment_id = fields.Many2one('elderly.appointment', string='來源預約單', readonly=True)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        # 如果支付狀態發生了變化
        if 'payment_state' in vals or 'state' in vals:
            print(111111111111111111111)
            for move in self:
                # 找到關聯的銷售訂單
                sale_orders = move.line_ids.mapped('sale_line_ids.order_id')
                # 找到這些銷售訂單關聯的預約單
                appointments = sale_orders.mapped('appointment_id')
                if appointments:
                    # 強制觸發重新計算
                    appointments._compute_payment_status()
        return res
