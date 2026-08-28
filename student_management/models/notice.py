from odoo import models, fields, api
from datetime import date

class StudentNotice(models.Model):
    _name = 'student.notice'
    _description = 'School Notice'
    _order = 'date desc, id desc' # Auto-sort: Most recent first

    name = fields.Char(string="Title", required=True)
    content = fields.Html(string="Notice Content")
    date = fields.Date(string="Post Date", default=fields.Date.context_today)
    expiry_date = fields.Date(string="Expiry Date")
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High')
    ], string="Priority", default='1')
    
    # Selection for targeting specific groups
    target_audience = fields.Selection([
        ('all', 'All'),
        ('students', 'Students Only'),
        ('teachers', 'Teachers Only')
    ], string="Visible To", default='all')

    active = fields.Boolean(default=True, string="Active")

    @api.model
    def _check_expirations(self):
        """ This can be used in a cron job or a filter to hide old notices """
        today = fields.Date.today()
        expired_notices = self.search([('expiry_date', '<', today), ('active', '=', True)])
        expired_notices.write({'active': False})