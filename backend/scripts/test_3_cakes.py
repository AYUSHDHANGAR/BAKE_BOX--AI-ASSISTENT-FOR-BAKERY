import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
import json
import re
from app.db import get_db, query_all

with get_db() as conn:
    rows = query_all(conn, "SELECT chunk_id, source_type, sku_or_title, chunk_text, metadata_json FROM BB_RAG_CHUNKS WHERE source_type IN ('CAKE', 'CUSTOM_CAKE')")
    cake_chunks = []
    for r in rows:
        meta = json.loads(r["METADATA_JSON"]) if r["METADATA_JSON"] else {}
        cake_chunks.append({
            "chunk_id": r["CHUNK_ID"],
            "source_type": r["SOURCE_TYPE"],
            "sku": r["SKU_OR_TITLE"],
            "text": r["CHUNK_TEXT"],
            "meta": meta
        })

print(f"Loaded {len(cake_chunks)} cake chunks.")

def find_3_cakes(query, existing=[]):
    q_lower = query.lower()
    selected = list(existing)
    seen = {c.get("sku_id") for c in selected if c.get("sku_id")}
    
    # Flavor list
    known_flavors = [
        "red velvet", "black forest", "white forest", "pineapple", "chocolate", 
        "truffle", "strawberry", "butterscotch", "vanilla", "mango", "blueberry", 
        "rasmalai", "gulab jamun", "kitkat", "oreo", "hazelnut", "fruit", "caramel"
    ]
    matched_flavor = None
    for f in known_flavors:
        if f in q_lower:
            matched_flavor = f
            break
            
    # 1. If flavor detected, find cakes with that exact flavor
    if matched_flavor:
        for c in cake_chunks:
            if len(selected) >= 3:
                break
            meta = c["meta"]
            sku = meta.get("sku_id")
            if sku in seen:
                continue
            f_name = (meta.get("flavor") or "").lower()
            name = (meta.get("name") or "").lower()
            if matched_flavor in f_name or matched_flavor in name:
                selected.append({
                    "sku_id": sku,
                    "name": meta.get("name"),
                    "flavor": meta.get("flavor"),
                    "category": meta.get("category"),
                    "weight_kg": meta.get("weight_kg", 0.5),
                    "price": float(meta.get("price", 249.0)),
                    "image_url": meta.get("image_path"),
                    "available_base_variants": meta.get("available_base_variants"),
                    "is_custom": c["source_type"] == "CUSTOM_CAKE"
                })
                seen.add(sku)
                
    # 2. General search by tokens if still < 3
    if len(selected) < 3:
        words = [w for w in re.findall(r'\w+', q_lower) if len(w) > 3 and w not in ["cake", "show", "batao", "chahiye", "dikhao", "some"]]
        for c in cake_chunks:
            if len(selected) >= 3:
                break
            meta = c["meta"]
            sku = meta.get("sku_id")
            if sku in seen:
                continue
            text = (meta.get("name", "") + " " + meta.get("flavor", "") + " " + meta.get("description", "")).lower()
            if any(w in text for w in words):
                selected.append({
                    "sku_id": sku,
                    "name": meta.get("name"),
                    "flavor": meta.get("flavor"),
                    "category": meta.get("category"),
                    "weight_kg": meta.get("weight_kg", 0.5),
                    "price": float(meta.get("price", 249.0)),
                    "image_url": meta.get("image_path"),
                    "available_base_variants": meta.get("available_base_variants"),
                    "is_custom": c["source_type"] == "CUSTOM_CAKE"
                })
                seen.add(sku)
                
    # 3. Fallback to any popular cakes
    for c in cake_chunks:
        if len(selected) >= 3:
            break
        meta = c["meta"]
        sku = meta.get("sku_id")
        if sku not in seen:
            selected.append({
                "sku_id": sku,
                "name": meta.get("name"),
                "flavor": meta.get("flavor"),
                "category": meta.get("category"),
                "weight_kg": meta.get("weight_kg", 0.5),
                "price": float(meta.get("price", 249.0)),
                "image_url": meta.get("image_path"),
                "available_base_variants": meta.get("available_base_variants"),
                "is_custom": c["source_type"] == "CUSTOM_CAKE"
            })
            seen.add(sku)
            
    return selected[:3]

# Test cases
for q in ["show me some red velvet cake", "mujhe black forest cake chahiye", "pineapple cake dikhao"]:
    res = find_3_cakes(q)
    print(f"\nQuery: '{q}' -> Returned {len(res)} cakes:")
    for i, c in enumerate(res):
        print(f"  {i+1}. {c['name']} ({c['flavor']}) | SKU: {c['sku_id']} | Price: Rs.{c['price']}")
