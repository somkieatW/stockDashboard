from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_folder='public')
CORS(app)

db_url = os.getenv('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(db_url)

@app.route('/')
def serve_index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('public', path)

@app.route('/api/config')
def get_config():
    return jsonify({
        "supabaseUrl": "https://bvgzgvqymubnpozcbnlc.supabase.co",
        "supabaseKey": os.getenv('SUPABASE_ANON_KEY', 'sb_secret_fruePNgz_NRQnVxGZeGWMw_W_Hj34p1')
    })

# --- PRODUCT PRESETS API ---
@app.route('/api/presets/products', methods=['GET'])
def get_product_presets():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT id, name, default_price as \"defaultPrice\" FROM product_presets ORDER BY name;")
        presets = cur.fetchall()
        # Convert numeric values to float for JSON serialization
        for p in presets:
            p['defaultPrice'] = float(p['defaultPrice'])
        return jsonify(presets)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/presets/products', methods=['POST'])
def save_product_preset():
    data = request.json
    id_val = data.get('id')
    name = data.get('name')
    default_price = data.get('defaultPrice')

    if not name or default_price is None:
        return jsonify({"error": "Missing name or defaultPrice"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if id_val:
            cur.execute(
                "INSERT INTO product_presets (id, name, default_price) VALUES (%s, %s, %s) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, default_price = EXCLUDED.default_price;",
                (id_val, name, default_price)
            )
        else:
            id_val = f"p-{int(os.urandom(4).hex(), 16)}"
            cur.execute(
                "INSERT INTO product_presets (id, name, default_price) VALUES (%s, %s, %s);",
                (id_val, name, default_price)
            )
        conn.commit()
        return jsonify({"status": "success", "id": id_val})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/presets/products/<id_val>', methods=['DELETE'])
def delete_product_preset(id_val):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM product_presets WHERE id = %s;", (id_val,))
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


# --- COST PRESETS API ---
@app.route('/api/presets/costs', methods=['GET'])
def get_cost_presets():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT id, name FROM cost_presets ORDER BY name;")
        presets = cur.fetchall()
        return jsonify(presets)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/presets/costs', methods=['POST'])
def save_cost_preset():
    data = request.json
    id_val = data.get('id')
    name = data.get('name')

    if not name:
        return jsonify({"error": "Missing name"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if id_val:
            cur.execute(
                "INSERT INTO cost_presets (id, name) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;",
                (id_val, name)
            )
        else:
            id_val = f"c-cat-{int(os.urandom(4).hex(), 16)}"
            cur.execute(
                "INSERT INTO cost_presets (id, name) VALUES (%s, %s);",
                (id_val, name)
            )
        conn.commit()
        return jsonify({"status": "success", "id": id_val})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/presets/costs/<id_val>', methods=['DELETE'])
def delete_cost_preset(id_val):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM cost_presets WHERE id = %s;", (id_val,))
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


# --- SALES API ---
@app.route('/api/sales', methods=['GET'])
def get_sales():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT id, TO_CHAR(date, 'YYYY-MM-DD') as date, name, price, sold FROM sales ORDER BY date DESC, id DESC;")
        sales = cur.fetchall()
        for s in sales:
            s['price'] = float(s['price'])
        return jsonify(sales)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/sales', methods=['POST'])
def add_sales():
    data = request.json
    id_val = data.get('id') or f"s-{int(os.urandom(4).hex(), 16)}"
    date = data.get('date')
    name = data.get('name')
    price = data.get('price')
    sold = data.get('sold')

    if not date or not name or price is None or sold is None:
        return jsonify({"error": "Missing required sales fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO sales (id, date, name, price, sold) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET date = EXCLUDED.date, name = EXCLUDED.name, price = EXCLUDED.price, sold = EXCLUDED.sold;",
            (id_val, date, name, price, sold)
        )
        conn.commit()
        return jsonify({"status": "success", "id": id_val})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/sales/<id_val>', methods=['DELETE'])
def delete_sales(id_val):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM sales WHERE id = %s;", (id_val,))
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


# --- COSTS API ---
@app.route('/api/costs', methods=['GET'])
def get_costs():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT id, TO_CHAR(date, 'YYYY-MM-DD') as date, name, category, cost, is_packaging as \"isPackaging\", qty, used, remaining, unit_cost as \"unitCost\", linked_products as \"linkedProducts\" FROM costs ORDER BY date DESC, id DESC;")
        costs = cur.fetchall()
        for c in costs:
            c['cost'] = float(c['cost'])
            if c['unitCost'] is not None:
                c['unitCost'] = float(c['unitCost'])
        return jsonify(costs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/costs', methods=['POST'])
def add_cost():
    data = request.json
    id_val = data.get('id') or f"c_rec{int(os.urandom(4).hex(), 16)}"
    date = data.get('date')
    name = data.get('name')
    category = data.get('category')
    cost = data.get('cost')
    is_packaging = data.get('isPackaging', False)
    qty = data.get('qty')
    used = data.get('used')
    remaining = data.get('remaining')
    unit_cost = data.get('unitCost')
    linked_products = data.get('linkedProducts')

    if not date or not name or not category or cost is None:
        return jsonify({"error": "Missing required cost fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO costs (id, date, name, category, cost, is_packaging, qty, used, remaining, unit_cost, linked_products)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (id) DO UPDATE SET
               date = EXCLUDED.date, name = EXCLUDED.name, category = EXCLUDED.category, cost = EXCLUDED.cost,
               is_packaging = EXCLUDED.is_packaging, qty = EXCLUDED.qty, used = EXCLUDED.used,
               remaining = EXCLUDED.remaining, unit_cost = EXCLUDED.unit_cost, linked_products = EXCLUDED.linked_products;""",
            (id_val, date, name, category, cost, is_packaging, qty, used, remaining, unit_cost, json.dumps(linked_products) if linked_products is not None else None)
        )
        conn.commit()
        return jsonify({"status": "success", "id": id_val})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/costs/<id_val>', methods=['DELETE'])
def delete_cost(id_val):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM costs WHERE id = %s;", (id_val,))
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


# --- RESET TO DEMO DATA ---
@app.route('/api/reset', methods=['POST'])
def reset_db():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Re-initialize the DB using initial data
        from init_db import default_product_presets, default_cost_presets, initial_sales, initial_costs
        
        cur.execute("TRUNCATE sales, costs, product_presets, cost_presets CASCADE;")

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
        return jsonify({"status": "success"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    # Ensure public folder exists
    os.makedirs('public', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
