from odoo import models, fields, api

class StudentParent(models.Model):
    _name = 'student.parent'
    _description = 'Student Parent / Guardian'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Parent Name", required=True, tracking=True)
    phone = fields.Char(string="Phone", required=True, tracking=True)
    email = fields.Char(string="Email")
    address = fields.Text(string="Address")
    
    relationship = fields.Selection([
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
        ('other', 'Other')
    ], string="Relationship", default='father')
    
    student_ids = fields.Many2many('student.student', 'student_parent_rel', 'parent_id', 'student_id', string="Linked Students")
    
    user_id = fields.Many2one('res.users', string="Portal User", help="Used for portal access")

    def action_create_user(self):
        for record in self:
            if record.user_id:
                continue
            group_portal = self.env.ref('base.group_portal', raise_if_not_found=False)
            group_parent = self.env.ref('student_management.group_parent', raise_if_not_found=False)
            user = self.env['res.users'].create({
                'name': record.name,
                'login': record.email or f"{record.name.lower().replace(' ', '.')}@parent.local",
                'groups_id': [(6, 0, [g.id for g in (group_portal, group_parent) if g])]
            })
            record.user_id = user.id
            if record.email:
                user.partner_id.email = record.email
                user.with_context(create_user=True).action_reset_password()
