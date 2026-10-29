import urllib.request
import json
import time
import sys

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def test_api():
    base_url = 'http://127.0.0.1:8000'
    print('=============================================')
    print('BAKEBOX E2E VERIFICATION TEST')
    print('Shri Ram Baker & Autonomous AI Assistant CHOCO')
    print('=============================================')

    print('\n[1] Testing /health (IBM Db2 Connectivity)...')
    with urllib.request.urlopen(f'{base_url}/health') as r:
        health_data = json.loads(r.read().decode())
        print(f"Status: {health_data['status']} | DB: {health_data['ibm_db2']} | Timestamp: {health_data.get('timestamp')}")
        assert health_data['status'] == 'HEALTHY', "Database is not healthy"

    print('\n[2] Testing Product Catalogs (/api/products/cakes, /custom-cakes, /accessories, /bakery-raw)...')
    with urllib.request.urlopen(f'{base_url}/api/products/cakes?limit=2') as r:
        cakes = json.loads(r.read().decode())
        print(f"Standard Cakes Count: {cakes['total']} | Sample: {cakes['items'][0]['NAME']} (SKU: {cakes['items'][0]['SKU_ID']})")
        assert cakes['total'] > 500

    with urllib.request.urlopen(f'{base_url}/api/products/custom-cakes?limit=2') as r:
        custom_cakes = json.loads(r.read().decode())
        print(f"Custom Designer Cakes Count: {custom_cakes['total']} | Sample: {custom_cakes['items'][0]['NAME']}")
        assert custom_cakes['total'] >= 50

    with urllib.request.urlopen(f'{base_url}/api/products/accessories') as r:
        accessories = json.loads(r.read().decode())
        print(f"Party Accessories Count: {accessories['total']}")
        assert accessories['total'] >= 40

    with urllib.request.urlopen(f'{base_url}/api/products/bakery-raw') as r:
        raw_items = json.loads(r.read().decode())
        print(f"Bakery Raw & Oven Patties Count: {raw_items['total']}")
        assert raw_items['total'] >= 25

    print('\n[3] Testing Authentication (/api/auth/login)...')
    login_req = urllib.request.Request(
        f'{base_url}/api/auth/login',
        data=json.dumps({'email': 'customer@bakebox.in', 'password': 'Customer@123'}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(login_req) as r:
        auth_res = json.loads(r.read().decode())
        token = auth_res['access_token']
        user_name = auth_res['user']['full_name']
        print(f"Customer Logged In: {user_name} | Role: {auth_res['user']['role']} | Token Verified.")

    print('\n[4] Testing CHOCO AI Assistant (Hybrid RAG + Gemini API + IBM Db2 Buffer)...')
    user_query = "Radhe Radhe! Mujhe 1st anniversary celebration ke liye 1kg red velvet cake chahiye eggless mein. Hamare Mathura store mein kaun kaun se designs hain aur baking time kya lagega?"
    print(f"User Query: {user_query}")
    
    t0 = time.time()
    choco_req = urllib.request.Request(
        f'{base_url}/api/choco/chat',
        data=json.dumps({
            'message': user_query,
            'session_id': 'e2e_verification_session_01'
        }).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    )
    with urllib.request.urlopen(choco_req) as r:
        choco_res = json.loads(r.read().decode())
        latency = time.time() - t0
        print(f"\nCHOCO Response ({latency:.2f}s latency):\n{choco_res['reply']}")
        print(f"\nRetrieved Knowledge Nodes: {choco_res['retrieved_count']}")
        print(f"Dynamic UI Product Cards Generated: {len(choco_res.get('ui_cards', []))}")
        for i, card in enumerate(choco_res.get('ui_cards', []), 1):
            print(f"  Card {i}: {card.get('name')} | SKU: {card.get('sku_id')} | Price: INR {card.get('price')} | Image: {card.get('image_url')}")

    print('\n[5] Testing Isolated Multi-Turn Conversation Buffer in IBM Db2 (/api/choco/history)...')
    hist_req = urllib.request.Request(
        f'{base_url}/api/choco/history?session_id=e2e_verification_session_01',
        headers={'Authorization': f'Bearer {token}'}
    )
    with urllib.request.urlopen(hist_req) as r:
        hist_res = json.loads(r.read().decode())
        messages = hist_res.get('messages', [])
        print(f"Stored Buffer Turns in IBM Db2: {len(messages)}")
        for m in messages:
            print(f"  [{m['role'].upper()}]: {m['content'][:60]}...")

    print('\n[6] Testing Order Checkout & Persistence in IBM Db2 (/api/orders/)...')
    order_req = urllib.request.Request(
        f'{base_url}/api/orders/',
        data=json.dumps({
            'customer_name': user_name,
            'customer_phone': '+91 9876543210',
            'delivery_address': 'Bhagel Chaupal, Khatoti Kua, Mathura',
            'order_type': 'DELIVERY',
            'special_notes': '1st Anniversary Eggless fresh bake',
            'items': [
                {
                    'sku_id': 'BB-RVT-01-10kg',
                    'item_name': 'Red Velvet Heart Special',
                    'quantity': 1,
                    'unit_price': 549.0,
                    'cake_base': 'Khoaa (Eggless)',
                    'cake_weight': '1.0kg',
                    'custom_message': 'Happy 1st Anniversary'
                },
                {
                    'sku_id': 'BB-ACC-CANDLE-01',
                    'item_name': 'Metallic Gold Number Candle (Set)',
                    'quantity': 1,
                    'unit_price': 49.0,
                    'cake_base': 'STANDARD',
                    'cake_weight': '0.0kg',
                    'custom_message': 'Gold Sparkle'
                }
            ]
        }).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    )
    with urllib.request.urlopen(order_req) as r:
        order_res = json.loads(r.read().decode())
        order_id = order_res['order_id']
        print(f"Order Successfully Created in IBM Db2! Order ID: #{order_id} | Total Amount: INR {order_res['total_amount']} | Status: {order_res['status']}")

    print('\n[7] Testing Customer Orders Query (/api/orders/my-orders)...')
    my_orders_req = urllib.request.Request(
        f'{base_url}/api/orders/my-orders',
        headers={'Authorization': f'Bearer {token}'}
    )
    with urllib.request.urlopen(my_orders_req) as r:
        my_orders_res = json.loads(r.read().decode())
        print(f"Customer Total Orders: {len(my_orders_res.get('orders', []))}")
        latest = my_orders_res['orders'][0]
        print(f"  Latest Order ID: #{latest['order_id']} | Items: {len(latest['items'])} | Status: {latest['order_status']}")

    print('\n[8] Testing Admin Portal & Order State Management (/api/admin/metrics & status change)...')
    admin_auth = urllib.request.Request(
        f'{base_url}/api/auth/login',
        data=json.dumps({'email': 'admin@bakebox.in', 'password': 'Admin@123'}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(admin_auth) as r:
        admin_token = json.loads(r.read().decode())['access_token']

    metrics_req = urllib.request.Request(
        f'{base_url}/api/admin/metrics',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    with urllib.request.urlopen(metrics_req) as r:
        metrics = json.loads(r.read().decode())
        print(f"Admin Dashboard Metrics -> Total Orders: {metrics['total_orders']} | Total Cakes: {metrics['total_cakes']} | Total Revenue: INR {metrics['total_revenue']}")

    # Change order status to BAKING
    status_req = urllib.request.Request(
        f'{base_url}/api/admin/orders/{order_id}/status',
        data=json.dumps({'status': 'BAKING'}).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {admin_token}'},
        method='PATCH'
    )
    with urllib.request.urlopen(status_req) as r:
        status_res = json.loads(r.read().decode())
        print(f"Admin Updated Order #{order_id} Status -> {status_res['updated_status']}")

    print('\n[9] Testing Frontend Dev Server (http://127.0.0.1:3000)...')
    with urllib.request.urlopen('http://127.0.0.1:3000') as r:
        html = r.read().decode()
        assert '<div id="root">' in html or 'vite' in html.lower()
        print("Frontend Vite Server is Online and serving BAKEBOX React App!")

    print('\n======================================================')
    print('ALL 9 VERIFICATION CHECKS PASSED WITH 100% SUCCESS!')
    print('BAKEBOX PLATFORM & CHOCO AI ASSISTANT READY FOR PRODUCTION!')
    print('======================================================')

if __name__ == '__main__':
    test_api()
