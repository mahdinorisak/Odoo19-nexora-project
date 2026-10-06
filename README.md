# Nexora App

Odoo 19 furniture app: sales, purchasing, inventory, manufacturing.

`odoo` `odoo19` `python` `erp`

A custom Odoo 19 application for a furniture business: manufacturing, customization and sales. Built step by step as a learning project.

## Features

- **Products:** categories, types, materials, images, automatic codes, margin, stock levels and low-stock flag
- **Printing / Customization:** printing types and options, chosen per sales order line
- **Customers and vendors:** types and categories, email validation, vendor ratings and lead times
- **Sales:** quotations and orders with a status workflow, discounts, taxes and computed totals
- **Purchasing:** purchase orders; receiving creates incoming stock
- **Inventory:** warehouses, locations, stock moves and a stock check
- **Manufacturing:** bills of materials and manufacturing orders that consume components and produce finished goods
- **Employees:** employees and a department tree
- **Security:** four access groups and record rules
- **Reports:** PDFs for sales, purchase and manufacturing orders, plus a stock report wizard
- **Dashboard:** graph and pivot analysis for sales, stock and production, plus a low-stock list
- **Purchase requests:** approval workflow that creates a purchase order
- **Inventory adjustments:** stock counts that post correction moves
- **Units of measure:** a unit on every product, shown on all order, BOM and stock lines
- **Custom designs, job positions and variants:** designs with images linked to products, job positions linked to employees, size and color variants with extra prices
- **Reports menu:** product, sales, purchase, inventory (SQL view) and production reports with pivot and graph views
- **Advanced:** model and view inheritance, a JSON route, an email template, a scheduled low-stock check and automated tests

## Requirements

- Odoo 19.0 (Community)
- Python 3.10+
- PostgreSQL
- `wkhtmltopdf` for PDF reports

## Installation

1. Copy this folder into your Odoo addons path.
2. Restart Odoo and update the Apps list (developer mode).
3. Install **Nexora App**.

## Demo data

Odoo 19 loads demo data only when asked. Create a fresh database with:

    python odoo-bin -c odoo.conf -d demo_db -i nexora_app --with-demo

## Tests

11 automated tests cover totals, stock moves, manufacturing and validation rules.

## Running the tests

```bash
python odoo-bin -c odoo.conf -d test_db -i nexora_app --test-tags /nexora_app --stop-after-init
```

## Roadmap

- Configuration menu and demo data
