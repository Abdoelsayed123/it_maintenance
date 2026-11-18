# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ItDevice(models.Model):
    _name = 'it.device'
    _description = 'IT Device'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = 'name, serial_number'
    _rec_names_search = ['name', 'serial_number']

    name = fields.Char(
        string='Device Name', required=True, tracking=True,
        help='Brand and model, e.g. "Dell Latitude 5420".')
    serial_number = fields.Char(required=True, copy=False, tracking=True)
    device_type = fields.Selection([
        ('laptop', 'Laptop'),
        ('desktop', 'Desktop'),
        ('printer', 'Printer'),
        ('screen', 'Screen'),
        ('network', 'Network Device'),
        ('server', 'Server'),
        ('other', 'Other'),
    ], required=True, default='laptop', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', index=True, tracking=True)
    location = fields.Char(help='Where the device is installed, e.g. "Accounts office, 2nd floor".')
    active = fields.Boolean(default=True, tracking=True)
    notes = fields.Text()

    company_id = fields.Many2one(
        'res.company', required=True, index=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    purchase_date = fields.Date()
    price = fields.Monetary(string='Purchase Price', currency_field='currency_id')
    warranty_end_date = fields.Date(string='Warranty Until', tracking=True)
    warranty_state = fields.Selection([
        ('none', 'No Warranty'),
        ('active', 'Under Warranty'),
        ('expired', 'Expired'),
    ], compute='_compute_warranty_state')

    request_ids = fields.One2many('it.request', 'device_id', string='Maintenance Requests')
    request_count = fields.Integer(compute='_compute_request_stats')
    open_request_count = fields.Integer(compute='_compute_request_stats')
    maintenance_cost = fields.Monetary(
        compute='_compute_request_stats', currency_field='currency_id',
        help='Total cost of all completed maintenance requests on this device.')

    _sql_constraints = [
        ('serial_number_company_uniq', 'unique(serial_number, company_id)',
         'A device with this serial number already exists.'),
    ]

    @api.depends('warranty_end_date')
    def _compute_warranty_state(self):
        today = fields.Date.context_today(self)
        for device in self:
            if not device.warranty_end_date:
                device.warranty_state = 'none'
            elif device.warranty_end_date >= today:
                device.warranty_state = 'active'
            else:
                device.warranty_state = 'expired'

    @api.depends('request_ids.state', 'request_ids.amount_total')
    def _compute_request_stats(self):
        for device in self:
            requests = device.request_ids
            device.request_count = len(requests)
            device.open_request_count = len(requests.filtered(lambda r: r.state not in ('done', 'cancel')))
            device.maintenance_cost = sum(requests.filtered(lambda r: r.state == 'done').mapped('amount_total'))

    @api.constrains('purchase_date', 'warranty_end_date')
    def _check_dates(self):
        today = fields.Date.context_today(self)
        for device in self:
            if device.purchase_date and device.purchase_date > today:
                raise ValidationError(_("The purchase date of %s cannot be in the future.", device.name))
            if device.purchase_date and device.warranty_end_date \
                    and device.warranty_end_date < device.purchase_date:
                raise ValidationError(_("The warranty of %s cannot end before its purchase date.", device.name))

    def name_get(self):
        return [(device.id, '%s [%s]' % (device.name, device.serial_number)) for device in self]

    def action_view_requests(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('it_maintenance.it_request_action')
        action['domain'] = [('device_id', '=', self.id)]
        action['context'] = {'default_device_id': self.id}
        return action
