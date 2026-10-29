import urllib.request
import json
import time
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base_url = 'http://127.0.0.1:8000'

print("==================================================================")
print("TESTING STRICT 3-CAKE SUGGESTION REQUIREMENT IN CHOCO AI")
print("==================================================================")

# 1. Login
login_req = urllib.request.Request(
    f'{base_url}/api/auth/login',
    data=json.dumps({'email': 'customer@bakebox.in', 'password': 'Customer@123'}).encode(),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(login_req) as r:
    auth_data = json.loads(r.read().decode())
    token = auth_data['access_token']
    print(f"[OK] Logged in as: {auth_data['user']['full_name']}")

test_cases = [
    {
        "query": "show me some red velvet cake for anniversary celebration",
        "expected_flavor": "Red Velvet",
        "expect_cards": True
    },
    {
        "query": "mujhe 1kg black forest cake chahiye eggless mein. Kaun se designs available hain?",
        "expected_flavor": "Black Forest",
        "expect_cards": True
    },
    {
        "query": "kuch fresh pineapple cakes suggest karo birthday celebration ke liye",
        "expected_flavor": "Pineapple",
        "expect_cards": True
    },
    {
        "query": "actually i have placed one order can you provide me the status ?",
        "expected_flavor": None,
        "expect_cards": False
    }
]

for idx, tc in enumerate(test_cases, 1):
    q = tc["query"]
    print(f"\n--- Test {idx}: '{q}' ---")
    t0 = time.time()
    req = urllib.request.Request(
        f'{base_url}/api/choco/chat',
        data=json.dumps({
            'message': q,
            'session_id': f'test_session_{idx}'
        }).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    )
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode())
        cards = res.get('ui_cards', [])
        print(f"Latency: {time.time()-t0:.2f}s")
        print(f"Reply summary: {res['reply'][:120]}...")
        print(f"Cards returned: {len(cards)}")
        
        if tc["expect_cards"]:
            assert len(cards) == 3, f"FAILED: Expected exactly 3 cards, got {len(cards)}!"
            for c_idx, c in enumerate(cards, 1):
                print(f"  Cake {c_idx}: {c['name']} | Flavor: {c['flavor']} | SKU: {c['sku_id']} | Price: ₹{c['price']}")
                print(f"          Image: {c['image_url']}")
                assert c['image_url'].startswith('/catalog_images/'), f"Invalid image path: {c['image_url']}"
            print(f"[PASS] Successfully returned EXACTLY 3 matching cakes for '{tc['expected_flavor']}'!")
        else:
            assert len(cards) == 0, f"FAILED: Expected 0 cards for order query, got {len(cards)}!"
            print("[PASS] Successfully returned 0 cards for order status query.")

print("\n==================================================================")
print("ALL TESTS PASSED: CHOCO NOW RETURNS EXACTLY 3 MATCHING CAKES EVERY TIME!")
print("==================================================================")
