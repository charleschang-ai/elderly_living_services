from odoo import models, fields, api, tools


class ElderlyAppointmentReport(models.Model):
    _name = 'elderly.appointment.report'
    _description = "預約分析報表"
    _auto = False
    _rec_name = 'date'

    # --- 維度字段 (Dimensions) ---
    date = fields.Datetime(string='預約日期', readonly=True)
    service_id = fields.Many2one('elderly.service', string='服務項目', readonly=True)
    user_id = fields.Many2one('res.users', string='申請人', readonly=True)
    state = fields.Selection([
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('sale', '已轉訂單'),
        ('cancel', '已取消')
    ], string='預約狀態', readonly=True)

    # --- 度量字段 (Measures) ---
    # nbr 對應原本的數量統計，price_total 對應金額
    nbr = fields.Integer(string='預約單量', readonly=True)
    price_total = fields.Float(string='金額總計', readonly=True)
    appointment_id = fields.Many2one('elderly.appointment', string='預約單', readonly=True)

    # 模仿 sale.report 的結構
    def _select(self):
        # 這裡定義 SQL 的 SELECT 部分
        # id 必須是唯一的，通常用 min(id)
        return """
            SELECT
                min(app.id) as id,
                app.start_time as date,
                app.service_id as service_id,
                app.user_id as user_id,
                app.state as state,
                count(*) as nbr,
                sum(srv.price) as price_total
        """

    def _from(self):
        # 定義 SQL 的 FROM 和 JOIN 部分
        return """
            FROM elderly_appointment app
            JOIN elderly_service srv ON (app.service_id = srv.id)
        """

    def _group_by(self):
        # 定義 SQL 的 GROUP BY 部分
        # 所有出現在 SELECT 但沒被聚合(sum/count)的字段都要放在這裡
        return """
            GROUP BY
                app.start_time,
                app.service_id,
                app.user_id,
                app.state
        """

    def init(self):
        # 執行 SQL 創建 View
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW %s AS (
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._group_by()))

    # 模仿 sale.report 點擊穿透回原始訂單的功能
    @api.readonly
    def action_open_appointment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'elderly.appointment',
            'view_mode': 'form',
            'res_id': self.appointment_id.id,
            'target': 'current',
        }
