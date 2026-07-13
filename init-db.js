const { Client } = require('pg');
require('dotenv').config();

const connectionString = process.env.DATABASE_URL || 'postgresql://postgres:tose0814239710@db.bvgzgvqymubnpozcbnlc.supabase.co:5432/postgres';

const client = new Client({
  connectionString,
  ssl: {
    rejectUnauthorized: false
  }
});

const defaultProductPresets = [
  { id: 'p1', name: 'ไก่ทอดหาดใหญ่แป้งกรอบ', defaultPrice: 45 },
  { id: 'p2', name: 'เฟรนช์ฟรายส์เขย่ารสชีส', defaultPrice: 35 },
  { id: 'p3', name: 'ลูกชิ้นแดงและไส้กรอกทอด', defaultPrice: 20 }
];

const defaultCostPresets = [
  { id: 'c1', name: 'วัตถุดิบหลัก (เนื้อสัตว์/แป้ง/ปรุงรส)' },
  { id: 'c2', name: 'น้ำมันพืชสำหรับทอด & แก๊สหุงต้ม' },
  { id: 'c3', name: 'กล่อง/ถุง/บรรจุภัณฑ์' },
  { id: 'c4', name: 'ต้นทุนคงที่ (ค่าที่เช่าร้านรายวัน/ค่าแรงช่วยเหลือ)' }
];

const initialSales = [
  { id: 's1', date: '2026-07-13', name: 'ไก่ทอดหาดใหญ่แป้งกรอบ', price: 45, sold: 120 },
  { id: 's2', date: '2026-07-12', name: 'เฟรนช์ฟรายส์เขย่ารสชีส', price: 35, sold: 90 },
  { id: 's3', date: '2026-07-10', name: 'ลูกชิ้นแดงและไส้กรอกทอด', price: 20, sold: 180 }
];

const initialCosts = [
  { id: 'c_rec1', date: '2026-07-13', name: 'สะโพกไก่และปีกไก่สดยกลัง (15 กก.)', category: 'วัตถุดิบหลัก (เนื้อสัตว์/แป้ง/ปรุงรส)', cost: 1650, isPackaging: false, qty: null, used: null, remaining: null, unitCost: null, linkedProducts: null },
  { id: 'c_rec2', date: '2026-07-13', name: 'กล่องกระดาษพรีเมียมใส่ไก่ทอด', category: 'กล่อง/ถุง/บรรจุภัณฑ์', cost: 100, isPackaging: true, qty: 20, used: 20, remaining: 0, unitCost: 5, linkedProducts: ['ไก่ทอดหาดใหญ่แป้งกรอบ'] },
  { id: 'c_rec3', date: '2026-07-12', name: 'น้ำมันพืชทอดอย่างดี (5 แกลลอน)', category: 'น้ำมันพืชสำหรับทอด & แก๊สหุงต้ม', cost: 265, isPackaging: false, qty: null, used: null, remaining: null, unitCost: null, linkedProducts: null },
  { id: 'c_rec4', date: '2026-07-12', name: 'ถุงหูหิ้วพลาสติกกันความร้อน', category: 'กล่อง/ถุง/บรรจุภัณฑ์', cost: 150, isPackaging: true, qty: 150, used: 150, remaining: 0, unitCost: 1, linkedProducts: ['all_menus'] },
  { id: 'c_rec5', date: '2026-07-10', name: 'จ่ายค่าเช่ารายวันล่วงหน้า 7 วัน', category: 'ต้นทุนคงที่ (ค่าที่เช่าร้านรายวัน/ค่าแรงช่วยเหลือ)', cost: 700, isPackaging: false, qty: null, used: null, remaining: null, unitCost: null, linkedProducts: null }
];

async function init() {
  try {
    console.log('Connecting to database...');
    await client.connect();
    console.log('Connected successfully!');

    // Clean up existing tables
    console.log('Dropping tables if exist...');
    await client.query('DROP TABLE IF EXISTS sales;');
    await client.query('DROP TABLE IF EXISTS costs;');
    await client.query('DROP TABLE IF EXISTS product_presets;');
    await client.query('DROP TABLE IF EXISTS cost_presets;');

    // Create tables
    console.log('Creating tables...');
    
    await client.query(`
      CREATE TABLE product_presets (
        id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        default_price NUMERIC(10, 2) NOT NULL
      );
    `);

    await client.query(`
      CREATE TABLE cost_presets (
        id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL
      );
    `);

    await client.query(`
      CREATE TABLE sales (
        id VARCHAR(50) PRIMARY KEY,
        date DATE NOT NULL,
        name VARCHAR(255) NOT NULL,
        price NUMERIC(10, 2) NOT NULL,
        sold INTEGER NOT NULL
      );
    `);

    await client.query(`
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
    `);

    console.log('Tables created successfully!');

    // Populate default product presets
    console.log('Inserting default product presets...');
    for (const p of defaultProductPresets) {
      await client.query(
        'INSERT INTO product_presets (id, name, default_price) VALUES ($1, $2, $3)',
        [p.id, p.name, p.defaultPrice]
      );
    }

    // Populate default cost presets
    console.log('Inserting default cost presets...');
    for (const c of defaultCostPresets) {
      await client.query(
        'INSERT INTO cost_presets (id, name) VALUES ($1, $2)',
        [c.id, c.name]
      );
    }

    // Populate initial sales
    console.log('Inserting initial sales records...');
    for (const s of initialSales) {
      await client.query(
        'INSERT INTO sales (id, date, name, price, sold) VALUES ($1, $2, $3, $4, $5)',
        [s.id, s.date, s.name, s.price, s.sold]
      );
    }

    // Populate initial costs
    console.log('Inserting initial costs records...');
    for (const c of initialCosts) {
      await client.query(
        'INSERT INTO costs (id, date, name, category, cost, is_packaging, qty, used, remaining, unit_cost, linked_products) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)',
        [c.id, c.date, c.name, c.category, c.cost, c.isPackaging, c.qty, c.used, c.remaining, c.unitCost, JSON.stringify(c.linkedProducts)]
      );
    }

    console.log('Database initialization complete!');
  } catch (error) {
    console.error('Error initializing database:', error);
  } finally {
    await client.end();
  }
}

init();
