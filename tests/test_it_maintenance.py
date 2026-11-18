# -*- coding: utf-8 -*-
from datetime import timedelta

from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestItMaintenance(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({'name': 'Test Customer', 'is_company': True})
        cls.device = cls.env['it.device'].create({
            'name': 'Test Laptop',
            'serial_number': 'TEST-SN-0001',
            'device_type': 'laptop',
            'partner_id': cls.customer.id,
        })
        cls.technician = new_test_user(
            cls.env, login='it_tech', groups='it_maintenance.group_it_technician')
        cls.other_technician = new_test_user(
            cls.env, login='it_tech_2', groups='it_maintenance.group_it_technician')

    def _create_request(self, **vals):
        return self.env['it.request'].create(dict({
            'name': 'Screen flickers',
            'device_id': self.device.id,
        }, **vals))

    def test_reference_is_generated(self):
        first = self._create_request()
        second = self._create_request()
        self.assertTrue(first.reference.startswith('REQ/'))
        self.assertNotEqual(first.reference, second.reference)
        self.assertEqual(first.partner_id, self.customer, "The customer comes from the device.")

    def test_amounts(self):
        request = self._create_request(labor_cost=250, line_ids=[
            fields.Command.create({'part_name': 'Screen', 'qty': 1, 'unit_price': 3200}),
            fields.Command.create({'part_name': 'Cable', 'qty': 2, 'unit_price': 50}),
        ])
        self.assertEqual(request.parts_total, 3300)
        self.assertEqual(request.amount_total, 3550)
        self.assertEqual(self.device.request_count, 1)
        self.assertEqual(self.device.open_request_count, 1)

    def test_workflow(self):
        request = self._create_request()
        request.with_user(self.technician).action_start()
        self.assertEqual(request.state, 'in_progress')
        self.assertEqual(request.user_id, self.technician, "Starting assigns the request to the technician.")
        self.assertTrue(request.date_start)

        request.action_wait_parts()
        self.assertEqual(request.state, 'waiting_parts')
        with self.assertRaises(UserError):
            request.action_done()

        request.action_start()
        request.action_done()
        self.assertEqual(request.state, 'done')
        self.assertTrue(request.date_done)
        self.assertEqual(self.device.maintenance_cost, request.amount_total)

        with self.assertRaises(UserError):
            request.action_cancel()

    def test_cancel_and_reset(self):
        request = self._create_request()
        request.action_cancel()
        self.assertEqual(request.state, 'cancel')
        request.action_reset_to_new()
        self.assertEqual(request.state, 'new')

    def test_cannot_delete_started_request(self):
        request = self._create_request()
        request.action_start()
        with self.assertRaises(UserError):
            request.unlink()
        request.action_cancel()
        request.unlink()
        self.assertFalse(request.exists())

    def test_deadline_before_request_date(self):
        with self.assertRaises(ValidationError):
            self._create_request(
                request_date=fields.Date.today(),
                deadline=fields.Date.today() - timedelta(days=1))

    def test_warranty_state(self):
        self.assertEqual(self.device.warranty_state, 'none')
        self.device.write({
            'purchase_date': fields.Date.today() - timedelta(days=30),
            'warranty_end_date': fields.Date.today() + timedelta(days=30),
        })
        self.assertEqual(self.device.warranty_state, 'active')
        with self.assertRaises(ValidationError):
            self.device.warranty_end_date = fields.Date.today() - timedelta(days=60)

    @mute_logger('odoo.sql_db')
    def test_serial_number_unique(self):
        with self.assertRaises(IntegrityError):
            self.env['it.device'].create({'name': 'Copy', 'serial_number': 'TEST-SN-0001'})
            self.env.flush_all()

    def test_technician_sees_own_and_unassigned_requests(self):
        own = self._create_request(user_id=self.technician.id)
        unassigned = self._create_request()
        other = self._create_request(user_id=self.other_technician.id)

        visible = self.env['it.request'].with_user(self.technician).search([])
        self.assertIn(own, visible)
        self.assertIn(unassigned, visible)
        self.assertNotIn(other, visible)

        own.with_user(self.technician).action_cancel()
        with self.assertRaises(AccessError, msg="Only managers can delete requests."):
            own.with_user(self.technician).unlink()
