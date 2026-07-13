import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from dotenv import load_dotenv
load_dotenv()

db_url = os.getenv('DATABASE_URL')

default_product_presets = [
    { 'id': 'p1', 'name': 'ไก่ทอดหาดใหญ่แป้งกรอบ', 'defaultPrice': 45 },
    { 'id': 'p2', 'name': 'เฟรนช์ฟรายส์เขย่ารสชีส', 'defaultPrice': 35 },
    { 'id': 'p3', 'name': 'ลูกชิ้นแดงและไส้กรอกทอด', 'defaultPrice': 20 }
]

default_cost_presets = [
    { 'id': 'c1', 'name': 'วัตถุดิบหลัก (เนื้อสัตว์/แป้ง/ปรุงรส)' },
    { 'id': 'c2', 'name': 'น้ำมันพืชสำหรับทอด & แก๊สหุงต้ม' },
    { 'id': 'c3', 'name': 'กล่อง/ถุง/บรรจุภัณฑ์' },
    { 'id': 'c4', 'name': 'ต้นทุนคงที่ (ค่าที่เช่าร้านรายวัน/ค่าแรงช่วยเหลือ)' }
]

initial_sales = [
    { 'id': 's1', 'date': '2026-07-13', 'name': 'ไก่ทอดหาดใหญ่แป้งกรอบ', 'price': 45, 'sold': 120 },
    { 'id': 's2', 'date': '2026-07-12', 'name': 'เฟรนช์ฟรายส์เขย่ารสชีส', 'price': 35, 'sold': 90 },
    { 'id': 's3', 'date': '2026-07-10', 'name': 'ลูกชิ้นแดงและไส้กรอกทอด', 'price': 20, 'sold': 180 }
]

initial_costs = [
    { 'id': 'c_rec1', 'date': '2026-07-13', 'name': 'สะโพกไก่และปีกไก่สดยกลัง (15 กก.)', 'category': 'วัตถุดิบหลัก (เนื้อสัตว์/แป้ง/ปรุงรส)', 'cost': 1650, 'isPackaging': False, 'qty': None, 'used': None, 'remaining': None, 'unitCost': None, 'linkedProducts': None },
    { 'id': 'c_rec2', 'date': '2026-07-13', 'name': 'กล่องกระดาษพรีเมียมใส่ไก่ทอด', 'category': 'กล่อง/ถุง/บรรจุภัณฑ์', 'cost': 100, 'isPackaging': True, 'qty': 20, 'used': 20, 'remaining': 0, 'unitCost': 5, 'linkedProducts': ['ไก่ทอดหาดใหญ่แป้งกรอบ'] },
    { 'id': 'c_rec3', 'date': '2026-07-12', 'name': 'น้ำมันพืชทอดอย่างดี (5 แกลลอน)', 'category': 'น้ำมันพืชสำหรับทอด & แก๊สหุงต้ม', 'cost': 265, 'isPackaging': False, 'qty': None, 'used': None, 'remaining': None, 'unitCost': None, 'linkedProducts': None },
    { 'id': 'c_rec4', 'date': '2026-07-12', 'name': 'ถุงหูหิ้วพลาสติกกันความร้อน', 'category': 'กล่อง/ถุง/บรรจุภัณฑ์', 'cost': 150, 'isPackaging': True, 'qty': 150, 'used': 150, 'remaining': 0, 'unitCost': 1, 'linkedProducts': ['all_menus'] },
    { 'id': 'c_rec5', 'date': '2026-07-10', 'name': 'จ่ายค่าเช่ารายวันล่วงหน้า 7 วัน', 'category': 'ต้นทุนคงที่ (ค่าที่เช่าร้านรายวัน/ค่าแรงช่วยเหลือ)', 'cost': 700, 'isPackaging': False, 'qty': None, 'used': None, 'remaining': None, 'unitCost': None, 'linkedProducts': None }
]

def init_db():
    try:
        print("Connecting to Supabase PostgreSQL database...")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        print("Connected successfully!")

        print("Dropping existing tables...")
        cur.execute("DROP TABLE IF EXISTS sales;")
        cur.execute("DROP TABLE IF EXISTS costs;")
        cur.execute("DROP TABLE IF EXISTS product_presets;")
        cur.execute("DROP TABLE IF EXISTS cost_presets;")

        print("Creating tables...")
        cur.execute("""
            CREATE TABLE product_presets (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                default_price NUMERIC(10, 2) NOT NULL
            );
        """)

        cur.execute("""
            CREATE TABLE cost_presets (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL
            );
        """)

        cur.execute("""
            CREATE TABLE sales (
                id VARCHAR(50) PRIMARY KEY,
                date DATE NOT NULL,
                name VARCHAR(255) NOT NULL,
                price NUMERIC(10, 2) NOT NULL,
                sold INTEGER NOT NULL
            );
        """)

        cur.execute("""
            CREATE TABLE costs (
                id VARCHAR(50) PRIMARY KEY,
                date DATE NOT NULL,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(255) NOT NULL,
                cost NUMERIC(10, 2) NOT NULL,
                is_packaging BOOLEAN NOT NULL DEFAULT FALSE,
                qty INTEGER,
                used INTEGER,
                remaining INTEGER,
                unit_cost NUMERIC(10, 2),
                linked_products JSONB
            );
        """)

        print("Populating initial data...")
        for p in default_product_presets:
            cur.execute(
                "INSERT INTO product_presets (id, name, default_price) VALUES (%s, %s, %s);",
                (p['id'], p['name'], p['defaultPrice'])
            )

        for c in default_cost_presets:
            cur.execute(
                "INSERT INTO cost_presets (id, name) VALUES (%s, %s);",
                (c['id'], c['name'])
            )

        for s in initial_sales:
            cur.execute(
                "INSERT INTO sales (id, date, name, price, sold) VALUES (%s, %s, %s, %s, %s);",
                (s['id'], s['date'], s['name'], s['price'], s['sold'])
            )

        for c in initial_costs:
            cur.execute(
                "INSERT INTO costs (id, date, name, category, cost, is_packaging, qty, used, remaining, unit_cost, linked_products) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
                (c['id'], c['date'], c['name'], c['category'], c['cost'], c['isPackaging'], c['qty'], c['used'], c['remaining'], c['unitCost'], json.dumps(c['linkedProducts']))
            )

        conn.commit()
        print("Database initialized successfully!")
    except Exception as e:
        print("Error during database initialization:", e)
    finally:
        if 'conn' in locals() and conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    init_db()
