from odoo import models, fields, api


class CampusLifeActivity(models.Model):
    _name = 'campus.life.activity'
    _description = 'Campus Life Activity'
    _inherit = ['mail.thread']
    _order = 'sequence, id'

    name = fields.Char(string='Title', required=True)
    sequence = fields.Integer(default=10)
    category = fields.Selection([
        ('clubs', 'Student Clubs'),
        ('athletics', 'Athletics'),
        ('arts', 'Arts & Culture'),
        ('housing', 'Housing'),
    ], string='Category', required=True, default='clubs')
    cover_image = fields.Image(string='Cover Image', max_width=1920, max_height=1920)
    gallery_image_1 = fields.Image(string='Gallery Image 1')
    gallery_image_2 = fields.Image(string='Gallery Image 2')
    gallery_image_3 = fields.Image(string='Gallery Image 3')
    gallery_image_4 = fields.Image(string='Gallery Image 4')
    summary = fields.Text(string='Short Summary')
    description = fields.Html(string='Full Description', sanitize_style=True)
    video_url = fields.Char(string='Video URL', help='YouTube or Vimeo URL')
    is_published = fields.Boolean(string='Published', default=False)
    website_url = fields.Char(string='Website URL', compute='_compute_website_url')

    def _compute_website_url(self):
        for record in self:
            record.website_url = f'/campus-life/{record.id}' if record.id else ''
