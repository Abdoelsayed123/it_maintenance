# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ItRequest(models.Model):
    _name = 'it.request'
    _description = 'Maintenance Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, request_date desc, id desc'
    _rec_names_search = ['reference', 'name']

    reference = fields.Char(
        required=True, readonly=True, copy=False, index=True, default=lambda self: _('New'))
    name = fields.Char(string='Subject', required=True, tracking=True)
    request_type = fields.Selection([
        ('repair', 'Repair'),
        ('installation', 'Installation'),
        ('preventive', 'Preventive Maintenance'),
        ('inspection', 'Inspection'),
    ], string='Type', required=True, default='repair', tracking=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], default='1', index=True, tracking=True)
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('waiting_parts', 'Waiting for Parts'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='new', required=True, index=True, copy=False, tracking=True,
        group_expand='_group_expand_states')
    color = fields.Integer()

    device_id = fields.Many2one(
        'it.device', required=True, index=True, ondelete='restrict', tracking=True)
    device_type = fields.Selection(related='device_id.device_type')
    partner_id = fields.Many2one(
        related='device_id.partner_id', string='Customer', store=True, index=True)
    user_id = fields.Many2one(
        'res.users', string='Technician', index=True, tracking=True,
        domain=lambda self: [('groups_id', 'in', self.env.ref('it_maintenance.group_it_technician').id)])

    request_date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    deadline = fields.Date(tracking=True)
    date_start = fields.Datetime(string='Started On', readonly=True, copy=False)
    date_done = fields.Datetime(string='Completed On', readonly=True, copy=False)
    is_overdue = fields.Boolean(compute='_compute_is_overdue')

    description = fields.Html(string='Problem Description')
    diagnosis = fields.Html(string='Technician Report', copy=False)
    line_ids = fields.One2many('it.request.line', 'request_id', string='Spare Parts', copy=True)

    company_id = fields.Many2one(
        'res.company', required=True, index=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    labor_hours = fields.Float()
    labor_cost = fields.Monetary(currency_field='currency_id', tracking=True)
    parts_total = fields.Monetary(
        compute='_compute_amounts', store=True, currency_field='currency_id')
    amount_total = fields.Monetary(
        string='Total', compute='_compute_amounts', store=True, currency_field='currency_id',
        tracking=True)

    def _group_expand_states(self, states, domain, order):
        # Always show the workflow columns in order in the kanban; "Cancelled" only when used.
        return [key for key, _label in self._fields['state'].selection if key != 'cancel' or key in states]

    @api.depends('line_ids.subtotal', 'labor_cost')
    def _compute_amounts(self):
        for request in self:
            request.parts_total = sum(request.line_ids.mapped('subtotal'))
            request.amount_total = request.parts_total + request.labor_cost

    @api.depends('deadline', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for request in self:
            request.is_overdue = bool(
                request.deadline and request.deadline < today
                and request.state not in ('done', 'cancel'))

    @api.constrains('request_date', 'deadline')
    def _check_deadline(self):
        for request in self:
            if request.deadline and request.deadline < request.request_date:
                raise ValidationError(_("The deadline cannot be before the request date."))

    @api.constrains('labor_hours', 'labor_cost')
    def _check_labor(self):
        for request in self:
            if request.labor_hours < 0 or request.labor_cost < 0:
                raise ValidationError(_("Labor hours and labor cost cannot be negative."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', _('New')) == _('New'):
                vals['reference'] = self.env['ir.sequence'].next_by_code('it.request') or _('New')
        return super().create(vals_list)

    def name_get(self):
        return [(request.id, '%s - %s' % (request.reference, request.name)) for request in self]

    def unlink(self):
        if any(request.state not in ('new', 'cancel') for request in self):
            raise UserError(_("You can only delete requests that are New or Cancelled. "
                              "Cancel the request first."))
        return super().unlink()

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------

    def _check_state(self, allowed_states, action_name):
        for request in self:
            if request.state not in allowed_states:
                raise UserError(_("%(reference)s cannot be %(action)s from the \"%(state)s\" state.",
                                  reference=request.reference, action=action_name,
                                  state=dict(self._fields['state'].selection)[request.state]))

    def action_start(self):
        self._check_state(('new', 'waiting_parts'), _("started"))
        for request in self:
            vals = {'state': 'in_progress'}
            if not request.date_start:
                vals['date_start'] = fields.Datetime.now()
            if not request.user_id:
                vals['user_id'] = self.env.user.id
            request.write(vals)

    def action_wait_parts(self):
        self._check_state(('in_progress',), _("put on hold"))
        self.write({'state': 'waiting_parts'})

    def action_done(self):
        self._check_state(('in_progress',), _("completed"))
        if any(not request.user_id for request in self):
            raise UserError(_("Assign a technician before completing the request."))
        self.write({'state': 'done', 'date_done': fields.Datetime.now()})

    def action_cancel(self):
        self._check_state(('new', 'in_progress', 'waiting_parts'), _("cancelled"))
        self.write({'state': 'cancel'})

    def action_reset_to_new(self):
        self._check_state(('cancel',), _("reset"))
        self.write({'state': 'new', 'date_start': False, 'date_done': False})
