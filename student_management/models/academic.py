from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StudentAcademicYear(models.Model):
    _name = 'student.academic.year'
    _description = 'Academic Year'
    _order = 'start_date desc'
    
    name = fields.Char(string='Academic Year', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    active = fields.Boolean(string='Active', default=True)
    is_current = fields.Boolean(string='Current Year', default=False)
    
    term_ids = fields.One2many('student.term', 'academic_year_id', string='Terms')
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("Start Date cannot be after End Date."))
                
    @api.constrains('is_current')
    def _check_single_current_year(self):
        for record in self:
            if record.is_current:
                # If this one is set to current, unset others
                others = self.search([('id', '!=', record.id), ('is_current', '=', True)])
                others.write({'is_current': False})

class StudentTerm(models.Model):
    _name = 'student.term'
    _description = 'Academic Term / Semester'
    _order = 'start_date asc'
    
    name = fields.Char(string='Term Name', required=True)
    academic_year_id = fields.Many2one('student.academic.year', string='Academic Year', required=True, ondelete='cascade')
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    active = fields.Boolean(string='Active', default=True)
    is_current = fields.Boolean(string='Current Term', default=False)
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("Start Date cannot be after End Date."))
                
    @api.constrains('start_date', 'end_date', 'academic_year_id')
    def _check_dates_within_year(self):
        for record in self:
            if record.academic_year_id:
                if record.start_date < record.academic_year_id.start_date or record.end_date > record.academic_year_id.end_date:
                    raise ValidationError(_("Term dates must fall within the Academic Year dates."))
                    
    @api.constrains('is_current')
    def _check_single_current_term(self):
        for record in self:
            if record.is_current:
                # If this one is set to current, unset others
                others = self.search([('id', '!=', record.id), ('is_current', '=', True)])
                others.write({'is_current': False})

class StudentGradeLevel(models.Model):
    _name = 'student.grade.level'
    _description = 'Grade Level'
    _order = 'sequence asc'
    
    name = fields.Char(string='Level Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10, help="Order of the grade level")
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)