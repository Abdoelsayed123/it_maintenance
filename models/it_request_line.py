# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ItRequestLine(models.Model):
    _name = 'it.request.line'
    _description = 'Maintenance Request Spare Part'
    _order = 'request_id, sequence, id'

    sequence = fields.Integer(default=10)
    request_id = fields.Many2one('it.request', required=True, index=True, ondelete='cascade')
    part_name = fields.Char(string='Spare Part', required=True)
    qty = fields.Float(string='Quantity', default=1.0, digits=(16, 2))
    currency_id = fields.Many2one(related='request_id.currency_id')
    unit_price = fields.Monetary(currency_field='currency_id')
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True, currency_field='currency_id')

    _sql_constraints = [
        ('qty_positive', 'CHECK(qty > 0)', 'The quantity of a spare part must be greater than zero.'),
        ('unit_price_positive', 'CHECK(unit_price >= 0)', 'The unit price cannot be negative.'),
    ]

    @api.depends('qty', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.qty * line.unit_price
