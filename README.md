<p align="center">
  <img src="static/description/icon.png" width="96" alt="IT Maintenance icon"/>
</p>

<h1 align="center">IT Maintenance for Odoo 16</h1>

<p align="center">
  An Odoo application for IT repair and maintenance companies: customer devices,
  repair requests, spare parts, technicians and printable job cards.
</p>

<p align="center">
  <img alt="Odoo 16" src="https://img.shields.io/badge/Odoo-16.0-714B67"/>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB"/>
  <img alt="License" src="https://img.shields.io/badge/License-LGPL--3-blue"/>
  <img alt="Tests" src="https://img.shields.io/badge/tests-9%20passing-brightgreen"/>
</p>

---

## Features

### Devices
- Device registry per customer: name, serial number, type, location, purchase price
- Warranty tracking with an automatic **Under Warranty / Expired** status
- Maintenance history, number of requests and total maintenance cost on each device
- Unique serial number per company, archiving, photo, chatter
- Kanban, list and form views with search by name **or** serial number

### Maintenance requests
- Automatic references: `REQ/2026/00001`
- Workflow: **New → In Progress → Waiting for Parts → Done** (or **Cancelled**)
- Request types: repair, installation, preventive maintenance, inspection
- Priorities (stars), deadlines and an automatic **Overdue** flag
- Spare parts lines with quantities and prices, labor hours and labor cost, automatic totals
- Technician report (diagnosis) separate from the customer's problem description
- Chatter with field tracking, followers and scheduled activities
- Kanban board grouped by status, plus list, calendar, pivot and graph views
- Printable **Job Card** (PDF) with customer, device, parts, totals and signatures

### Security
| Group | Can do |
|---|---|
| **Technician** | Sees requests assigned to them or not yet assigned; creates and works on requests and devices |
| **Manager** | Sees everything, can delete, and has access to the Reporting menu |

Multi-company record rules are included.

---

## Screenshots

> Add your own screenshots in `static/description/` and reference them here, for example:
>
> `![Kanban](static/description/screenshot_kanban.png)`

---

## Installation

1. Copy the `it_maintenance` folder into a directory listed in your `addons_path`.
2. Restart Odoo.
3. Activate the developer mode, then go to **Apps → Update Apps List**.
4. Search for **IT Maintenance** and click **Activate**.

The module depends only on `base` and `mail`.

Install it on a database **with demo data** to get sample customers, devices and requests.

### Running the tests

```bash
python odoo-bin -c odoo.conf -d test_db -i it_maintenance --test-enable --test-tags /it_maintenance --stop-after-init
```

---

## Technical overview

```
it_maintenance/
├── models/
│   ├── it_device.py          # it.device
│   ├── it_request.py         # it.request (workflow, totals, references)
│   └── it_request_line.py    # it.request.line (spare parts)
├── views/                    # list, form, kanban, calendar, pivot, graph, search, menus
├── report/                   # QWeb PDF job card
├── security/                 # groups, access rights, record rules
├── data/                     # ir.sequence for request references
├── demo/                     # sample customers, devices and requests
├── migrations/16.0.1.0.0/    # upgrade script from version 0.1
└── tests/                    # 9 automated tests
```

Odoo features used: `mail.thread` and `mail.activity.mixin`, `image.mixin`, computed and stored fields,
`@api.constrains`, SQL constraints, `ir.sequence`, `group_expand`, record rules, `_rec_names_search`,
QWeb reports, migration scripts and `TransactionCase` tests.

---

## Author

**Abdelrahman Elsayed**: [GitHub](https://github.com/Abdoelsayed123)

License: [LGPL-3](https://www.gnu.org/licenses/lgpl-3.0.html)
