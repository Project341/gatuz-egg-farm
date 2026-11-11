GATUZ EGG FARM - POULTRY FARM MANAGEMENT SYSTEM
================================================
Windows desktop app | Python + CustomTkinter + SQLite

DEFAULT FARMS
- Farm 1
- Farm 2
- Farm 3
These are created automatically on first launch. If an older database already has
farm records, the first three existing farm records are renamed in place so their
IDs and linked chicken/production/sales history remain connected.

EGG SIZE CATEGORIES
- Small
- Medium
- Large
- Jumbo
Inventory is tracked by individual egg pieces. One tray = 30 pieces.
Older Dirty inventory is retained internally during database upgrade for historical
compatibility, but the current production, sales, and inventory screens use the four
requested sellable sizes above.

INSTALLATION ON WINDOWS
1. Install Python 3.11 or newer and enable Add Python to PATH.
2. Extract this ZIP to a writable folder.
3. Double-click SETUP_AND_RUN.bat for first-time setup and launch.
4. For later use, double-click run.bat.
Do not open main.py directly in Python IDLE. The launcher uses the private .venv
and installs requirements if necessary. Internet is required for first-time package
installation; after installation, the app works offline.

FIRST LOGIN
Username: admin
Password: admin123
Change the password immediately after first login.

PERSISTENT DATABASE
%LOCALAPPDATA%\EGG_FARM_GATUZ\database\egg_farm_gatuz.db
Backups are stored in %LOCALAPPDATA%\EGG_FARM_GATUZ\backup.
The app upgrades an existing database on startup by adding Large and Jumbo egg
columns and expanding inventory categories without intentionally deleting records.
Please create a backup before replacing an older app folder.

CURRENT MODULES
- Dashboard with Farm 1/Farm 2/Farm 3 cards and farm overview
- Farm/extension, chicken, customer, supplier, expense, and feed item records
- Morning and afternoon egg collection by farm and egg size
- Egg inventory by Small, Medium, Large, and Jumbo
- Sales in pieces or trays with automatic stock deduction and payment status
- Inventory adjustments with negative-stock prevention
- Financial summary and Excel/PDF export
- Admin/staff login, password change, audit log, backup and restore

NOTE
This is an updated application package, but it has not been validated on your own
Windows PC. Test with sample records first and keep regular database backups.


UPDATE: CRACKED EGGS INVENTORY
- Egg inventory includes Small, Medium, Large, Jumbo, and Cracked Eggs.
- Record Cracked Eggs during morning/afternoon collection; they are added to separate Cracked Eggs stock.
- Cracked Eggs can be adjusted, damaged, or discarded in Egg Inventory.
- Cracked Eggs are tracked separately and are not included in regular sales sizes.
- Existing database records are preserved; the app adds the new category and production field at startup.
