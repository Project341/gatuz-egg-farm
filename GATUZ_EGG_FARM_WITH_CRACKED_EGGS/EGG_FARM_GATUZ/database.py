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
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,salt TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN ('ADMIN','STAFF')),active INTEGER DEFAULT 1,created_at TEXT);
CREATE TABLE IF NOT EXISTS extensions(id INTEGER PRIMARY KEY,code TEXT UNIQUE NOT NULL,name TEXT NOT NULL,location TEXT,breed TEXT,established TEXT,assigned_staff INTEGER REFERENCES users(id),status TEXT DEFAULT 'Active',notes TEXT);
CREATE TABLE IF NOT EXISTS chickens(id INTEGER PRIMARY KEY,chicken_code TEXT UNIQUE NOT NULL,breed TEXT NOT NULL,quantity INTEGER NOT NULL CHECK(quantity>=0),age_months INTEGER DEFAULT 0,acquired_date TEXT,laying_hens INTEGER DEFAULT 0 CHECK(laying_hens>=0),extension_id INTEGER REFERENCES extensions(id),status TEXT DEFAULT 'Active',notes TEXT);
CREATE TABLE IF NOT EXISTS production(id INTEGER PRIMARY KEY,extension_id INTEGER NOT NULL REFERENCES extensions(id),collection_date TEXT NOT NULL,shift TEXT NOT NULL CHECK(shift IN ('Morning','Afternoon')),small INTEGER DEFAULT 0 CHECK(small>=0),medium INTEGER DEFAULT 0 CHECK(medium>=0),large INTEGER DEFAULT 0 CHECK(large>=0),jumbo INTEGER DEFAULT 0 CHECK(jumbo>=0),cracked INTEGER NOT NULL DEFAULT 0 CHECK(cracked>=0),dirty INTEGER DEFAULT 0 CHECK(dirty>=0),recorded_by INTEGER REFERENCES users(id),created_at TEXT,UNIQUE(extension_id,collection_date,shift));
CREATE TABLE IF NOT EXISTS inventory(category TEXT PRIMARY KEY CHECK(category IN ('Small','Medium','Large','Jumbo','Cracked Eggs','Dirty')),quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0));
CREATE TABLE IF NOT EXISTS inventory_tx(id INTEGER PRIMARY KEY,category TEXT NOT NULL,quantity INTEGER NOT NULL,tx_type TEXT NOT NULL,tx_date TEXT NOT NULL,extension_id INTEGER REFERENCES extensions(id),reference TEXT,notes TEXT,user_id INTEGER REFERENCES users(id));
CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY,name TEXT NOT NULL,contact TEXT,address TEXT,notes TEXT);
CREATE TABLE IF NOT EXISTS sales(id INTEGER PRIMARY KEY,invoice TEXT UNIQUE NOT NULL,customer_id INTEGER REFERENCES customers(id),sale_date TEXT NOT NULL,category TEXT NOT NULL,quantity INTEGER NOT NULL CHECK(quantity>0),unit TEXT NOT NULL CHECK(unit IN ('piece','tray')),price_per_unit REAL NOT NULL CHECK(price_per_unit>=0),total REAL NOT NULL,paid REAL DEFAULT 0,payment_status TEXT,notes TEXT,user_id INTEGER REFERENCES users(id));
CREATE TABLE IF NOT EXISTS suppliers(id INTEGER PRIMARY KEY,name TEXT NOT NULL,contact TEXT,address TEXT,products TEXT,notes TEXT);
CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY,expense_date TEXT NOT NULL,category TEXT NOT NULL,description TEXT,amount REAL NOT NULL CHECK(amount>=0),extension_id INTEGER REFERENCES extensions(id),supplier_id INTEGER REFERENCES suppliers(id),user_id INTEGER REFERENCES users(id));
CREATE TABLE IF NOT EXISTS feed_items(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL,feed_type TEXT,unit TEXT DEFAULT 'kg',stock REAL DEFAULT 0 CHECK(stock>=0),low_stock REAL DEFAULT 0,cost_per_unit REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS feed_tx(id INTEGER PRIMARY KEY,feed_id INTEGER REFERENCES feed_items(id),tx_date TEXT,tx_type TEXT,quantity REAL CHECK(quantity>0),unit_cost REAL,supplier_id INTEGER REFERENCES suppliers(id),extension_id INTEGER REFERENCES extensions(id),notes TEXT,user_id INTEGER REFERENCES users(id));
CREATE TABLE IF NOT EXISTS mortality(id INTEGER PRIMARY KEY,chicken_id INTEGER REFERENCES chickens(id),extension_id INTEGER REFERENCES extensions(id),quantity INTEGER CHECK(quantity>0),date TEXT,reason TEXT,recorded_by INTEGER REFERENCES users(id));
CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY,user_id INTEGER,action TEXT,details TEXT,created_at TEXT);
CREATE INDEX IF NOT EXISTS idx_prod_date ON production(collection_date); CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);
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
    sqlrow = c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='inventory'").fetchone()
    inventory_sql = (sqlrow['sql'] or '') if sqlrow else ''
    if sqlrow and "'Cracked Eggs'" not in inventory_sql:
        c.execute('ALTER TABLE inventory RENAME TO inventory_old')
        c.execute("""CREATE TABLE inventory(
            category TEXT PRIMARY KEY CHECK(category IN
            ('Small','Medium','Large','Jumbo','Cracked Eggs','Dirty')),
            quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0))""")
        oldcols = {r['name'] for r in c.execute('PRAGMA table_info(inventory_old)').fetchall()}
        if {'category','quantity'} <= oldcols:
            c.execute('INSERT OR IGNORE INTO inventory(category,quantity) SELECT category,quantity FROM inventory_old')
        c.execute('DROP TABLE inventory_old')
    for cat in EGG_INVENTORY_CATEGORIES:
        c.execute('INSERT OR IGNORE INTO inventory(category,quantity) VALUES(?,0)', (cat,))
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
                c.execute('UPDATE inventory SET quantity=quantity+? WHERE category=?', (n, cat))
                c.execute('INSERT INTO inventory_tx(category,quantity,tx_type,tx_date,extension_id,reference,user_id) VALUES(?,?,?,?,?,?,?)',
                          (cat, n, 'Collection', dt, eid, shift, uid))
    return sum(q)

def record_sale(cid, dt, cat, qty, unit, price, paid, uid, notes=''):
    qty, price, paid = int(qty), float(price), float(paid)
    pieces = qty * (30 if unit == 'tray' else 1)
    total = qty * price
    if cat not in EGG_SIZES or qty <= 0 or price < 0 or paid < 0 or unit not in ('piece', 'tray'):
        raise ValueError('Invalid egg size, quantity, unit, or amount.')
    with connect() as c:
        r = c.execute('SELECT quantity FROM inventory WHERE category=?', (cat,)).fetchone()
        if not r or r['quantity'] < pieces:
            raise ValueError(f'Insufficient {cat} stock. Available: {r["quantity"] if r else 0} pieces.')
        inv = 'GATUZ-' + datetime.now().strftime('%Y%m%d%H%M%S%f')
        status = 'Paid' if paid >= total else ('Partial' if paid > 0 else 'Unpaid')
        c.execute('INSERT INTO sales(invoice,customer_id,sale_date,category,quantity,unit,price_per_unit,total,paid,payment_status,notes,user_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                  (inv, cid, dt, cat, qty, unit, price, total, paid, status, notes, uid))
        c.execute('UPDATE inventory SET quantity=quantity-? WHERE category=?', (pieces, cat))
        c.execute('INSERT INTO inventory_tx(category,quantity,tx_type,tx_date,reference,user_id) VALUES(?,?,?,?,?,?)',
                  (cat, -pieces, 'Sale', dt, inv, uid))
    return inv, total

def adjust_inventory(cat, qty, kind, dt, uid, notes=''):
    qty = int(qty)
    if cat not in EGG_INVENTORY_CATEGORIES or cat == 'Dirty' or qty <= 0 or kind not in ('Damage', 'Discard', 'Adjustment In', 'Adjustment Out'):
        raise ValueError('Select a valid egg size and enter a positive quantity.')
    delta = qty if kind == 'Adjustment In' else -qty
    with connect() as c:
        r = c.execute('SELECT quantity FROM inventory WHERE category=?', (cat,)).fetchone()
        if not r or r['quantity'] + delta < 0:
            raise ValueError('Insufficient inventory; negative stock is not allowed.')
        c.execute('UPDATE inventory SET quantity=quantity+? WHERE category=?', (delta, cat))
        c.execute('INSERT INTO inventory_tx(category,quantity,tx_type,tx_date,notes,user_id) VALUES(?,?,?,?,?,?)',
                  (cat, delta, kind, dt, notes, uid))

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
