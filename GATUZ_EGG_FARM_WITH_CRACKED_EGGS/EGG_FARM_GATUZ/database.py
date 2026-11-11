import sqlite3, os
from pathlib import Path
from datetime import datetime

APP_DIR = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'EGG_FARM_GATUZ'
DB_DIR = APP_DIR / 'database'
BACKUP_DIR = APP_DIR / 'backup'
DB_PATH = DB_DIR / 'egg_farm_gatuz.db'
EGG_SIZES = ('Small', 'Medium', 'Large', 'Jumbo')
EGG_INVENTORY_CATEGORIES = (*EGG_SIZES, 'Cracked Eggs', 'Dirty')

SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,salt TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN ('ADMIN','STAFF')),active INTEGER NOT NULL DEFAULT 1,created_at TEXT);
CREATE TABLE IF NOT EXISTS extensions(id INTEGER PRIMARY KEY,code TEXT UNIQUE NOT NULL,name TEXT NOT NULL,location TEXT,breed TEXT,established TEXT,status TEXT DEFAULT 'Active',notes TEXT,assigned_staff INTEGER REFERENCES users(id));
CREATE TABLE IF NOT EXISTS chickens(id INTEGER PRIMARY KEY,chicken_code TEXT UNIQUE NOT NULL,breed TEXT NOT NULL,quantity INTEGER NOT NULL CHECK(quantity>=0),age_months INTEGER DEFAULT 0,acquired_date TEXT,laying_hens INTEGER DEFAULT 0,extension_id INTEGER REFERENCES extensions(id),status TEXT,notes TEXT);
CREATE TABLE IF NOT EXISTS production(id INTEGER PRIMARY KEY,extension_id INTEGER NOT NULL REFERENCES extensions(id),collection_date TEXT NOT NULL,shift TEXT NOT NULL CHECK(shift IN ('Morning','Afternoon')),small INTEGER NOT NULL DEFAULT 0 CHECK(small>=0),medium INTEGER NOT NULL DEFAULT 0 CHECK(medium>=0),large INTEGER NOT NULL DEFAULT 0 CHECK(large>=0),jumbo INTEGER NOT NULL DEFAULT 0 CHECK(jumbo>=0),cracked INTEGER NOT NULL DEFAULT 0 CHECK(cracked>=0),dirty INTEGER NOT NULL DEFAULT 0 CHECK(dirty>=0),recorded_by INTEGER REFERENCES users(id),created_at TEXT);
CREATE TABLE IF NOT EXISTS inventory(category TEXT PRIMARY KEY CHECK(category IN ('Small','Medium','Large','Jumbo','Cracked Eggs','Dirty')),quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0));
CREATE TABLE IF NOT EXISTS farm_inventory(id INTEGER PRIMARY KEY,extension_id INTEGER NOT NULL REFERENCES extensions(id),category TEXT NOT NULL CHECK(category IN ('Small','Medium','Large','Jumbo','Cracked Eggs')),quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0),UNIQUE(extension_id, category));
CREATE TABLE IF NOT EXISTS inventory_tx(id INTEGER PRIMARY KEY,category TEXT NOT NULL,quantity INTEGER NOT NULL,tx_type TEXT NOT NULL,tx_date TEXT NOT NULL,extension_id INTEGER REFERENCES extensions(id),reference TEXT,notes TEXT,user_id INTEGER REFERENCES users(id));
CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY,name TEXT NOT NULL,contact TEXT,address TEXT,notes TEXT);
CREATE TABLE IF NOT EXISTS sales(id INTEGER PRIMARY KEY,invoice TEXT UNIQUE NOT NULL,customer_id INTEGER REFERENCES customers(id),sale_date TEXT NOT NULL,category TEXT NOT NULL,quantity INTEGER NOT NULL CHECK(quantity>0),unit TEXT NOT NULL CHECK(unit IN ('piece','tray')),price_per_unit REAL NOT NULL CHECK(price_per_unit>=0),total REAL NOT NULL CHECK(total>=0),paid REAL NOT NULL DEFAULT 0 CHECK(paid>=0),payment_status TEXT DEFAULT 'Unpaid',notes TEXT,user_id INTEGER REFERENCES users(id),extension_id INTEGER REFERENCES extensions(id));
CREATE TABLE IF NOT EXISTS suppliers(id INTEGER PRIMARY KEY,name TEXT NOT NULL,contact TEXT,address TEXT,products TEXT,notes TEXT);
CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY,expense_date TEXT NOT NULL,category TEXT NOT NULL,description TEXT,amount REAL NOT NULL CHECK(amount>=0),extension_id INTEGER REFERENCES extensions(id));
CREATE TABLE IF NOT EXISTS feed_items(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL,feed_type TEXT,unit TEXT DEFAULT 'kg',stock REAL DEFAULT 0 CHECK(stock>=0),low_stock REAL DEFAULT 0,cost_per_unit REAL DEFAULT 0,created_at TEXT);
CREATE TABLE IF NOT EXISTS feed_tx(id INTEGER PRIMARY KEY,feed_id INTEGER REFERENCES feed_items(id),tx_date TEXT,tx_type TEXT,quantity REAL CHECK(quantity>0),unit_cost REAL,supplier_id INTEGER REFERENCES suppliers(id),notes TEXT);
CREATE TABLE IF NOT EXISTS mortality(id INTEGER PRIMARY KEY,chicken_id INTEGER REFERENCES chickens(id),extension_id INTEGER REFERENCES extensions(id),quantity INTEGER CHECK(quantity>0),date TEXT,reason TEXT,notes TEXT);
CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY,user_id INTEGER,action TEXT,details TEXT,created_at TEXT);
CREATE INDEX IF NOT EXISTS idx_prod_date ON production(collection_date); 
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date); 
'''


def connect():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=20)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('PRAGMA journal_mode=WAL')
    return c


def _migrate(c):
    pcols = {r['name'] for r in c.execute('PRAGMA table_info(production)').fetchall()}
    for col in ('large', 'jumbo', 'cracked'):
        if col not in pcols:
            c.execute(f'ALTER TABLE production ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0 CHECK({col}>=0)')

    sales_cols = {r['name'] for r in c.execute('PRAGMA table_info(sales)').fetchall()}
    if 'extension_id' not in sales_cols:
        c.execute('ALTER TABLE sales ADD COLUMN extension_id INTEGER REFERENCES extensions(id)')

    tx_cols = {r['name'] for r in c.execute('PRAGMA table_info(inventory_tx)').fetchall()}
    if 'extension_id' not in tx_cols:
        c.execute('ALTER TABLE inventory_tx ADD COLUMN extension_id INTEGER REFERENCES extensions(id)')

    sqlrow = c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='inventory'").fetchone()
    inventory_sql = (sqlrow['sql'] or '') if sqlrow else ''
    if sqlrow and "'Cracked Eggs'" not in inventory_sql:
        c.execute('ALTER TABLE inventory RENAME TO inventory_old')
        c.execute("""CREATE TABLE inventory(
            category TEXT PRIMARY KEY CHECK(category IN
            ('Small','Medium','Large','Jumbo','Cracked Eggs','Dirty')),
            quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0))""")
        oldcols = {r['name'] for r in c.execute('PRAGMA table_info(inventory_old)').fetchall()}
        if {'category', 'quantity'} <= oldcols:
            c.execute('INSERT OR IGNORE INTO inventory(category,quantity) SELECT category,quantity FROM inventory_old')
        c.execute('DROP TABLE inventory_old')

    c.execute("""CREATE TABLE IF NOT EXISTS farm_inventory(
        id INTEGER PRIMARY KEY,
        extension_id INTEGER NOT NULL REFERENCES extensions(id),
        category TEXT NOT NULL CHECK(category IN ('Small','Medium','Large','Jumbo','Cracked Eggs')),
        quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0),
        UNIQUE(extension_id, category)
    )""")

    for cat in (*EGG_SIZES, 'Cracked Eggs'):
        c.execute('INSERT OR IGNORE INTO inventory(category,quantity) VALUES(?,0)', (cat,))
        for row in c.execute('SELECT id FROM extensions ORDER BY id').fetchall():
            c.execute('INSERT OR IGNORE INTO farm_inventory(extension_id,category,quantity) VALUES(?,?,0)', (row['id'], cat))

    # Move any legacy global inventory into Farm 1 if the app already has data but no farm inventory values.
    default_ext = c.execute('SELECT id FROM extensions ORDER BY id LIMIT 1').fetchone()
    if default_ext:
        for cat in (*EGG_SIZES, 'Cracked Eggs'):
            total = c.execute('SELECT quantity FROM inventory WHERE category=?', (cat,)).fetchone()
            if total and total['quantity'] > 0:
                c.execute('UPDATE farm_inventory SET quantity=? WHERE extension_id=? AND category=?', (total['quantity'], default_ext['id'], cat))

    existing = c.execute('SELECT id FROM extensions ORDER BY id LIMIT 3').fetchall()
    for idx, row in enumerate(existing, 1):
        c.execute('UPDATE extensions SET name=?, code=? WHERE id=?', (f'Farm {idx}', f'FARM-{idx}', row['id']))
    for idx in range(len(existing) + 1, 4):
        c.execute('INSERT OR IGNORE INTO extensions(code,name,location,breed,status,notes) VALUES(?,?,?,?,?,?)',
                  (f'FARM-{idx}', f'Farm {idx}', '', 'Layer', 'Active', 'Default farm location'))


def init_db():
    from security import make_password
    with connect() as c:
        c.executescript(SCHEMA)
        _migrate(c)
        if not c.execute('SELECT 1 FROM users').fetchone():
            h, s = make_password('admin123')
            c.execute('INSERT INTO users(username,password_hash,salt,role,created_at) VALUES(?,?,?,?,?)',
                      ('admin', h, s, 'ADMIN', datetime.now().isoformat()))


def audit(uid, action, details=''):
    with connect() as c:
        c.execute('INSERT INTO audit_log(user_id,action,details,created_at) VALUES(?,?,?,?)',
                  (uid, action, details, datetime.now().isoformat()))


def add_production(eid, dt, shift, small, medium, large, jumbo, cracked, uid):
    q = list(map(int, (small, medium, large, jumbo, cracked)))
    if min(q) < 0 or sum(q) == 0:
        raise ValueError('Enter non-negative quantities and at least one egg.')
    with connect() as c:
        c.execute('INSERT INTO production(extension_id,collection_date,shift,small,medium,large,jumbo,cracked,recorded_by,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',
                  (eid, dt, shift, *q, uid, datetime.now().isoformat()))
        for cat, n in zip((*EGG_SIZES, 'Cracked Eggs'), q):
            if n:
                c.execute('INSERT OR IGNORE INTO farm_inventory(extension_id,category,quantity) VALUES(?,?,0)', (eid, cat))
                c.execute('UPDATE farm_inventory SET quantity=quantity+? WHERE extension_id=? AND category=?', (n, eid, cat))
                c.execute('UPDATE inventory SET quantity=quantity+? WHERE category=?', (n, cat))
                c.execute('INSERT INTO inventory_tx(category,quantity,tx_type,tx_date,extension_id,reference,user_id) VALUES(?,?,?,?,?,?,?)',
                          (cat, n, 'Collection', dt, eid, shift, uid))
    return sum(q)


def record_sale(cid, dt, cat, qty, unit, price, paid, uid, notes='', extension_id=None):
    qty, price, paid = int(qty), float(price), float(paid)
    pieces = qty * (30 if unit == 'tray' else 1)
    total = qty * price
    if cat not in EGG_SIZES or qty <= 0 or price < 0 or paid < 0 or unit not in ('piece', 'tray'):
        raise ValueError('Invalid egg size, quantity, unit, or amount.')

    with connect() as c:
        if extension_id is not None:
            c.execute('INSERT OR IGNORE INTO farm_inventory(extension_id,category,quantity) VALUES(?,?,0)', (extension_id, cat))
            r = c.execute('SELECT quantity FROM farm_inventory WHERE extension_id=? AND category=?', (extension_id, cat)).fetchone()
            if not r or r['quantity'] < pieces:
                raise ValueError(f'Insufficient {cat} stock for Farm {extension_id}. Available: {r["quantity"] if r else 0} pieces.')
            c.execute('UPDATE farm_inventory SET quantity=quantity-? WHERE extension_id=? AND category=?', (pieces, extension_id, cat))
        else:
            r = c.execute('SELECT quantity FROM inventory WHERE category=?', (cat,)).fetchone()
            if not r or r['quantity'] < pieces:
                raise ValueError(f'Insufficient {cat} stock. Available: {r["quantity"] if r else 0} pieces.')
            c.execute('UPDATE inventory SET quantity=quantity-? WHERE category=?', (pieces, cat))

        inv = 'GATUZ-' + datetime.now().strftime('%Y%m%d%H%M%S%f')
        status = 'Paid' if paid >= total else ('Partial' if paid > 0 else 'Unpaid')
        c.execute('INSERT INTO sales(invoice,customer_id,sale_date,category,quantity,unit,price_per_unit,total,paid,payment_status,notes,user_id,extension_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                  (inv, cid, dt, cat, qty, unit, price, total, paid, status, notes, uid, extension_id))
        if extension_id is None:
            c.execute('UPDATE inventory SET quantity=quantity-? WHERE category=?', (pieces, cat))
        c.execute('INSERT INTO inventory_tx(category,quantity,tx_type,tx_date,extension_id,reference,user_id) VALUES(?,?,?,?,?,?,?)',
                  (cat, -pieces, 'Sale', dt, extension_id, inv, uid))
    return inv, total


def adjust_inventory(cat, qty, kind, dt, uid, notes='', extension_id=None):
    qty = int(qty)
    if cat not in EGG_INVENTORY_CATEGORIES or cat == 'Dirty' or qty <= 0 or kind not in ('Damage', 'Discard', 'Adjustment In', 'Adjustment Out'):
        raise ValueError('Select a valid egg size and enter a positive quantity.')
    delta = qty if kind == 'Adjustment In' else -qty
    with connect() as c:
        if extension_id is not None:
            c.execute('INSERT OR IGNORE INTO farm_inventory(extension_id,category,quantity) VALUES(?,?,0)', (extension_id, cat))
            r = c.execute('SELECT quantity FROM farm_inventory WHERE extension_id=? AND category=?', (extension_id, cat)).fetchone()
            if not r or r['quantity'] + delta < 0:
                raise ValueError('Insufficient farm inventory; negative stock is not allowed.')
            c.execute('UPDATE farm_inventory SET quantity=quantity+? WHERE extension_id=? AND category=?', (delta, extension_id, cat))
        else:
            r = c.execute('SELECT quantity FROM inventory WHERE category=?', (cat,)).fetchone()
            if not r or r['quantity'] + delta < 0:
                raise ValueError('Insufficient inventory; negative stock is not allowed.')
            c.execute('UPDATE inventory SET quantity=quantity+? WHERE category=?', (delta, cat))
        c.execute('INSERT INTO inventory_tx(category,quantity,tx_type,tx_date,extension_id,notes,user_id) VALUES(?,?,?,?,?,?,?)',
                  (cat, delta, kind, dt, extension_id, notes, uid))


def backup_database(destination=None):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dest = Path(destination) if destination else BACKUP_DIR / f'backup_{datetime.now():%Y%m%d_%H%M%S}.db'
    dest.parent.mkdir(parents=True, exist_ok=True)
    with connect() as src:
        dst = sqlite3.connect(dest)
        src.backup(dst)
        dst.close()
    return dest


def restore_database(source):
    source = Path(source)
    if not source.exists():
        raise FileNotFoundError(source)
    t = sqlite3.connect(source)
    check = t.execute('PRAGMA integrity_check').fetchone()[0]
    t.close()
    if check != 'ok':
        raise ValueError('Backup integrity check failed.')
    backup_database()
    src = sqlite3.connect(source)
    dst = sqlite3.connect(DB_PATH)
    src.backup(dst)
    dst.close()
    src.close()


def get_farm_inventory(extension_id=None):
    with connect() as c:
        if extension_id is None:
            return c.execute("SELECT category, SUM(quantity) AS quantity FROM farm_inventory GROUP BY category ORDER BY CASE category WHEN 'Small' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Large' THEN 3 WHEN 'Jumbo' THEN 4 WHEN 'Cracked Eggs' THEN 5 END").fetchall()
        return c.execute("SELECT category, quantity FROM farm_inventory WHERE extension_id=? ORDER BY CASE category WHEN 'Small' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Large' THEN 3 WHEN 'Jumbo' THEN 4 WHEN 'Cracked Eggs' THEN 5 END", (extension_id,)).fetchall()


def get_farm_inventory_tx(extension_id=None):
    with connect() as c:
        if extension_id is None:
            return c.execute('SELECT id,category,quantity,tx_type,tx_date,extension_id,reference,notes FROM inventory_tx ORDER BY id DESC LIMIT 100').fetchall()
        return c.execute('SELECT id,category,quantity,tx_type,tx_date,extension_id,reference,notes FROM inventory_tx WHERE extension_id=? ORDER BY id DESC LIMIT 100', (extension_id,)).fetchall()


# Legacy compatibility for older screens and exports.
__all__ = [
    'connect', 'init_db', 'audit', 'add_production', 'record_sale', 'adjust_inventory',
    'backup_database', 'restore_database', 'get_farm_inventory', 'get_farm_inventory_tx',
    'APP_DIR', 'DB_DIR', 'BACKUP_DIR', 'DB_PATH', 'EGG_SIZES', 'EGG_INVENTORY_CATEGORIES'
]

