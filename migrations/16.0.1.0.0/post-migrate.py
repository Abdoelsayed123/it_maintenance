# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Continue the reference numbering after the requests created before the upgrade.
    cr.execute("SELECT COALESCE(MAX(id), 0) FROM it_request")
    next_number = cr.fetchone()[0] + 1
    sequence = env['ir.sequence'].search([('code', '=', 'it.request')], limit=1)
    if sequence and sequence.number_next < next_number:
        sequence.number_next = next_number

    # Requests created during this upgrade (e.g. new demo data) were numbered before the
    # sequence was moved forward: give the newer duplicates a fresh reference.
    cr.execute("""
        SELECT id FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY reference ORDER BY id) AS rank
              FROM it_request
        ) ranked
         WHERE rank > 1
         ORDER BY id
    """)
    for (request_id,) in cr.fetchall():
        env['it.request'].browse(request_id).reference = sequence.next_by_id()
