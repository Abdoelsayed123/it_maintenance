# -*- coding: utf-8 -*-
"""Upgrade databases that ran version 0.1 of the module.

Fills the new required columns from the old data before the ORM adds
NOT NULL constraints, so existing devices and requests are kept.
"""


def _column_exists(cr, table, column):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = %s AND column_name = %s
    """, (table, column))
    return bool(cr.fetchone())


def migrate(cr, version):
    if not version:
        return

    # The scaffold model "it_maintenance" was removed (it never had a menu or a view).
    cr.execute("DROP TABLE IF EXISTS it_maintenance")

    # it.device: name (from the "Model - Owner" notes), active (was is_active)
    cr.execute("ALTER TABLE it_device ADD COLUMN IF NOT EXISTS name VARCHAR")
    cr.execute("""
        UPDATE it_device
           SET serial_number = 'UNKNOWN-' || id
         WHERE serial_number IS NULL OR serial_number = ''
    """)
    cr.execute("""
        UPDATE it_device
           SET name = CASE WHEN position(' - ' IN COALESCE(notes, '')) > 0
                           THEN split_part(notes, ' - ', 1)
                           ELSE serial_number END
         WHERE name IS NULL
    """)
    cr.execute("UPDATE it_device SET device_type = 'other' WHERE device_type IS NULL")
    if not _column_exists(cr, 'it_device', 'active'):
        cr.execute("ALTER TABLE it_device ADD COLUMN active BOOLEAN")
        if _column_exists(cr, 'it_device', 'is_active'):
            cr.execute("UPDATE it_device SET active = COALESCE(is_active, TRUE)")
        else:
            cr.execute("UPDATE it_device SET active = TRUE")

    # it.request: priority keys changed to the standard '0'..'3'
    cr.execute("""
        UPDATE it_request
           SET priority = CASE priority WHEN 'low' THEN '0'
                                        WHEN 'urgent' THEN '3'
                                        ELSE '1' END
         WHERE priority IS NULL OR priority NOT IN ('0', '1', '2', '3')
    """)
    cr.execute("""
        UPDATE it_request
           SET request_date = COALESCE(create_date::date, CURRENT_DATE)
         WHERE request_date IS NULL
    """)
    cr.execute("UPDATE it_request SET state = 'new' WHERE state IS NULL")
    cr.execute("UPDATE it_request SET name = 'Request ' || id WHERE name IS NULL OR name = ''")
    cr.execute("ALTER TABLE it_request ADD COLUMN IF NOT EXISTS reference VARCHAR")
    cr.execute("""
        UPDATE it_request
           SET reference = 'REQ/' || EXTRACT(YEAR FROM request_date)::int || '/' || lpad(id::text, 5, '0')
         WHERE reference IS NULL
    """)

    # it.request.line: part name is now required
    cr.execute("UPDATE it_request_line SET part_name = 'Spare part' WHERE part_name IS NULL OR part_name = ''")
    cr.execute("UPDATE it_request_line SET qty = 1 WHERE qty IS NULL OR qty <= 0")
