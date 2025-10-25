# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is an **Odoo 18** instance running in Docker, designed for **cyber cafe management** (Vietnamese: "quán nét"). The project manages customers, gaming accounts, sessions, transactions, and accounting for internet gaming centers.

## Architecture

### Docker Setup
- **Odoo**: Port 8069 (main application)
- **PostgreSQL**: Database backend
- **Mailpit**: Port 8025 (email testing)
- Custom addons mounted at `/mnt/extra-addons`

### Module Structure

The system follows Odoo's modular architecture with two types of modules:

1. **Cyber Cafe Modules** (custom business logic):
   - `customer_segment` - Customer segmentation based on play time
   - `cyber_customer` - Customer management (inherits from `res.partner`)
   - `cyber_account` - Gaming accounts linked to customers
   - `cyber_session` - Game session management with machine assignments
   - `cyber_transaction` - Transaction history (top-ups, spending)
   - `cyber_product` - Product/machine management
   - `cyber_expense` - Expense tracking
   - `cyber_maintenance` - Maintenance management
   - `cyber_report` - Custom reporting

2. **Accounting Modules** (community/third-party):
   - `om_account_accountant` - Core accounting features
   - `om_account_asset` - Asset management
   - `om_account_budget` - Budget management
   - `om_account_daily_reports` - Daily financial reports
   - `om_account_followup` - Customer follow-up
   - `om_fiscal_year` - Fiscal year management
   - `om_recurring_payments` - Recurring payment handling
   - `accounting_pdf_reports` - PDF report generation

### Data Model Relationships

**Core entities and their relationships:**

```
customer_segment (base segmentation)
    ↓ (Many2one)
cyber_customer (inherits res.partner)
    ↓ (One2many)
cyber_account (gaming accounts)
    ↓ (One2many)
cyber_session (play sessions)
    ↓ (Many2one to product.product)
product.product (machines with is_machine flag)
```

**Key inheritance patterns:**
- `cyber_customer` uses `_inherits` to extend `res.partner` with delegation inheritance
- `cyber_session` uses `_inherit` with `mail.thread` for activity tracking

**Automatic calculations:**
- Customer segments auto-assign based on `total_play_time` thresholds
- Customer totals recalculate when accounts are created/updated/deleted
- Session costs compute from duration × price_per_hour
- Account balances update on session closure and transactions

## Development Commands

### Starting the Environment
```powershell
docker-compose up -d
```

### Stopping the Environment
```powershell
docker-compose down
```

### Viewing Logs
```powershell
docker-compose logs -f web
```

### Accessing Odoo Shell (Python REPL)
```powershell
docker exec -it odoo odoo shell -d postgres
```

### Updating Module Lists
```powershell
docker exec -it odoo odoo -d postgres -u <module_name> --stop-after-init
```

### Database Operations
Connect to PostgreSQL:
```powershell
docker exec -it <postgres_container_name> psql -U odoo -d postgres
```

## Module Development Guidelines

### File Structure for Custom Modules
```
module_name/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── model_name.py
├── views/
│   └── model_views.xml
└── security/
    └── ir.model.access.csv
```

### Manifest File Requirements
- `name`: Display name
- `depends`: List parent modules (minimum: `['base']`)
- `data`: XML files in load order (security first, then views)
- `application`: True for top-level modules
- `installable`: True to enable installation

### Model Naming Conventions
- Model names: `cyber.model_name` (snake_case with dots)
- Python classes: `CyberModelName` (PascalCase)
- Fields: Use snake_case
- Vietnamese field labels are acceptable (already in use)

### Common Patterns in This Codebase

**Computing totals across relationships:**
```python
def _calculate_totals(self):
    for customer in self:
        accounts = self.env['cyber.account'].search([('customer_id', '=', customer.id)])
        customer.total_play_time = sum(acc.play_time_total for acc in accounts)
```

**Triggering parent recalculations on CRUD:**
```python
def write(self, vals):
    res = super().write(vals)
    for record in self:
        record.customer_id._calculate_totals()
    return res
```

**Monetary fields:**
Always pair with `currency_id`:
```python
total_cost = fields.Monetary(string='Total Cost', currency_field='currency_id')
currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
```

## Key Technical Details

### Odoo Version
- **Odoo 18.0** (Official Docker image)
- Uses Python 3.x (Odoo 18 requires Python 3.10+)

### Database
- **PostgreSQL** with credentials defined in docker-compose.yaml
- Database name: `postgres`
- User/Password: `odoo/odoo`

### Important Directories
- `addons/`: Custom module development
- `filestore/`: File storage (gitignored)
- `sessions/`: Session data (gitignored)
- `odoo-db-data/`: Database persistence (gitignored)

### Module Dependencies
When creating new modules:
1. Declare dependencies in `__manifest__.py` `depends` list
2. Ensure parent modules are installed first
3. Use `cyber_customer` as base for customer-related features
4. Use `customer_segment` for segmentation features

### View Definitions
- Form views: Detailed record editing
- Tree/List views: Record listings (note: `<list>` in XML, not `<tree>`)
- Use `<notebook>` and `<page>` for tabbed interfaces
- Access rights defined in `security/ir.model.access.csv`

## Common Issues

### Module Not Appearing
1. Check `__manifest__.py` syntax
2. Restart Odoo container: `docker-compose restart web`
3. Update apps list in Odoo UI (Apps menu → Update Apps List)

### Model Conflicts
- Multiple modules define `cyber.account` (in both `cyber_account` and `cyber_session`)
- This creates duplicate model definitions - ensure only one active implementation

### Database Changes Not Reflecting
- Upgrade module: `docker exec -it odoo odoo -d postgres -u module_name --stop-after-init`
- Or use Odoo UI: Apps → Search module → Upgrade

### Access Rights Issues
- Ensure `ir.model.access.csv` exists and is listed in `__manifest__.py`
- Format: `id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink`

## URLs
- **Odoo Application**: http://localhost:8069
- **Mailpit (Email Testing)**: http://localhost:8025
- **Database**: localhost:5432 (default PostgreSQL port)
