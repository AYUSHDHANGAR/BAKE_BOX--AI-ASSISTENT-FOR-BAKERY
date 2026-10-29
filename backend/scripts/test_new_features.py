import urllib.request
import json
import time
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base_url = 'http://127.0.0.1:8000'

print('==================================================')
print('TESTING BAKEBOX NEW FEATURES & HACKATHON READINESS')
print('==================================================')

# 1. Login as customer
login_req = urllib.request.Request(
    f'{base_url}/api/auth/login',
    data=json.dumps({'email': 'customer@bakebox.in', 'password': 'Customer@123'}).encode(),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(login_req) as r:
    auth_data = json.loads(r.read().decode())
    token = auth_data['access_token']
    print(f"[OK] Customer Logged In: {auth_data['user']['full_name']} (ID: {auth_data['user']['id']})")

# 2. Test CHOCO order status response (Case A: User has placed an order in IBM Db2)
print("\n--- Test 1: Order Status Query (With Live IBM Db2 Order) ---")
t0 = time.time()
req1 = urllib.request.Request(
    f'{base_url}/api/choco/chat',
    data=json.dumps({
        'message': 'actually i have placed one order can you provide me the status ?',
        'session_id': 'hackathon_session_01'
    }).encode(),
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
)
with urllib.request.urlopen(req1) as r:
    res1 = json.loads(r.read().decode())
    print(f"Latency: {time.time()-t0:.2f}s")
    print(f"CHOCO Response:\n{res1['reply']}")
    print(f"Self-Evaluation Result: {res1.get('self_eval')}")

# 3. Test CHOCO catalog query with fast latency
print("\n--- Test 2: Standard Cake Inquiry & Fast Retrieval ---")
t0 = time.time()
req2 = urllib.request.Request(
    f'{base_url}/api/choco/chat',
    data=json.dumps({
        'message': 'Radhe Radhe! Mujhe 1kg black forest cake chahiye eggless mein. Kaun se designs available hain?',
        'session_id': 'hackathon_session_01'
    }).encode(),
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
)
with urllib.request.urlopen(req2) as r:
    res2 = json.loads(r.read().decode())
    print(f"Latency: {time.time()-t0:.2f}s")
    print(f"CHOCO Response:\n{res2['reply'][:300]}...")
    print(f"Cards returned: {len(res2.get('ui_cards', []))}")
    if res2.get('ui_cards'):
        print(f"Card 1: {res2['ui_cards'][0]['name']} | Price: ₹{res2['ui_cards'][0]['price']} | Image: {res2['ui_cards'][0]['image_url']}")

# 4. Verify catalog size
print("\n--- Test 3: Catalog Size Verification (All 600+ Cakes) ---")
with urllib.request.urlopen(f'{base_url}/api/products/cakes') as r:
    cakes = json.loads(r.read().decode())
    print(f"Standard Cakes total count in IBM Db2: {cakes['total']}")
    print(f"Cakes returned in items array: {len(cakes['items'])}")

with urllib.request.urlopen(f'{base_url}/api/products/custom-cakes') as r:
    custom = json.loads(r.read().decode())
    print(f"Custom Designer Cakes total in IBM Db2: {custom['total']}")

print("\n==================================================")
print("ALL TESTS COMPLETED SUCCESSFULLY!")
print("==================================================")
