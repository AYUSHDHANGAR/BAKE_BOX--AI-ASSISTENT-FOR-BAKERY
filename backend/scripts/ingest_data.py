"""
BAKEBOX Data Ingestion and RAG Chunks Builder.
Ingests CSV records, parses policy PDFs, generates dense vector embeddings via BAAI/bge-small-en-v1.5,
and populates relational tables and RAG chunk store inside IBM Db2 (IBMDB201).
"""
import os
import csv
import json
import urllib.parse
import pypdf
import bcrypt
import ibm_db
from fastembed import TextEmbedding

DB2_CONN_STR = "DATABASE=IBMDB201;HOSTNAME=127.0.0.1;PORT=50000;PROTOCOL=TCPIP;UID=dbayush;PWD=8844;"
DATA_DIR = "IBM_RAG_DATA tables & pdf"
CATALOG_DIR = "BAKEBOX_CATALOG"
SUPABASE_PREFIX = "https://drrwmheivhcxfvkstcus.supabase.co/storage/v1/object/public/images_BAKEBOX/BAKEBOX_CATALOG/"

def get_db_conn():
    return ibm_db.connect(DB2_CONN_STR, "", "")

def normalize_image_path(img_url: str) -> str:
    if not img_url:
        return ""
    if img_url.startswith(SUPABASE_PREFIX):
        rel = urllib.parse.unquote(img_url.replace(SUPABASE_PREFIX, ""))
        return f"/catalog_images/{rel}"
    if img_url.startswith("BAKEBOX_CATALOG/"):
        rel = img_url.replace("BAKEBOX_CATALOG/", "")
        return f"/catalog_images/{rel}"
    return img_url

def ingest_admin_operators(conn):
    csv_path = os.path.join(DATA_DIR, "admin_family_operators_rows (1).csv")
    print(f"Ingesting Admin Operators from {csv_path}...")
    sql = """
        INSERT INTO BB_ADMIN_OPERATORS 
        (admin_id, operator_name, phone, role, assigned_branch, can_edit_prices, can_toggle_inventory, can_accept_orders, can_upload_photos)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    stmt = ibm_db.prepare(conn, sql)
    count = 0
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            admin_id = int(row["admin_id"])
            op_name = row["operator_name"]
            phone = row["phone"]
            role = row["role"]
            branch = row["assigned_branch"]
            can_edit = 1 if row.get("can_edit_prices", "false").lower() == "true" else 0
            can_toggle = 1 if row.get("can_toggle_inventory", "true").lower() == "true" else 0
            can_accept = 1 if row.get("can_accept_orders", "true").lower() == "true" else 0
            can_upload = 1 if row.get("can_upload_photos", "false").lower() == "true" else 0
            
            ibm_db.execute(stmt, (admin_id, op_name, phone, role, branch, can_edit, can_toggle, can_accept, can_upload))
            count += 1
    print(f"-> Ingested {count} Admin Operators.")

def seed_users(conn):
    print("Seeding default authentication accounts...")
    users = [
        ("admin@bakebox.in", "Admin@123", "Shri Ram Master Baker (Owner)", "+91 9528702189", "ADMIN"),
        ("operator@bakebox.in", "Operator@123", "Store Operator (Front Counter)", "+91 8923701210", "STORE_OPERATOR"),
        ("customer@bakebox.in", "Customer@123", "Rahul Sharma (Customer)", "+91 9876543210", "CUSTOMER"),
    ]
    sql = "INSERT INTO BB_USERS (email, password_hash, full_name, phone, role) VALUES (?, ?, ?, ?, ?)"
    stmt = ibm_db.prepare(conn, sql)
    for email, pwd, name, phone, role in users:
        p_hash = bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        try:
            ibm_db.execute(stmt, (email, p_hash, name, phone, role))
            print(f"-> Created user {email} ({role})")
        except Exception as e:
            print(f"User {email} creation note: {e}")

def ingest_cakes(conn):
    csv_path = os.path.join(DATA_DIR, "cakes_rows (6).csv")
    print(f"Ingesting Standard Cakes from {csv_path}...")
    sql = """
        INSERT INTO BB_CAKES 
        (sku_id, design_code, name, category, flavor, sub_category, available_base_variants, weight_kg, price, servings, has_chocochip, visual_features, image_path, prep_time, order_confirmation, description, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """
    stmt = ibm_db.prepare(conn, sql)
    count = 0
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row["sku_id"]
            d_code = row.get("design_code", "")
            name = row["name"]
            cat = row.get("category", "")
            flavor = row.get("flavor", "")
            sub_cat = row.get("sub_category", "")
            variants = row.get("available_base_variants", "")
            weight = float(row["weight_kg"]) if row.get("weight_kg") else 0.5
            price = float(row["price"]) if row.get("price") else 249.0
            servings = row.get("servings", "")
            has_chocochip = 1 if row.get("has_chocochip", "").lower() == "true" else 0
            features = row.get("visual_features", "")
            img_path = normalize_image_path(row.get("image_path", ""))
            prep_time = row.get("prep_time", "3-4 hours")
            confirmation = row.get("order_confirmation", "")
            desc = row.get("description", "")
            
            ibm_db.execute(stmt, (sku, d_code, name, cat, flavor, sub_cat, variants, weight, price, servings, has_chocochip, features, img_path, prep_time, confirmation, desc))
            count += 1
    print(f"-> Ingested {count} Standard Cakes.")

def ingest_custom_cakes(conn):
    csv_path = os.path.join(DATA_DIR, "custom_cakes_catalog_rows (1).csv")
    print(f"Ingesting Custom Designer Cakes from {csv_path}...")
    sql = """
        INSERT INTO BB_CUSTOM_CAKES
        (id, sku_id, design_code, name, category, flavor, sub_category, available_base_variants, service_type, weight_kg, servings, has_chocochip, visual_features, image_path, prep_time, order_confirmation, description, price_inr, pricing_type, ordering_channel, customization_options, price_status, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """
    stmt = ibm_db.prepare(conn, sql)
    count = 0
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = int(row["id"])
            sku = row["sku_id"]
            d_code = row.get("design_code", "")
            name = row["name"]
            cat = row.get("category", "")
            flavor = row.get("flavor", "")
            sub_cat = row.get("sub_category", "")
            variants = row.get("available_base_variants", "")
            service = row.get("service_type", "")
            weight = float(row["weight_kg"]) if row.get("weight_kg") else 1.0
            servings = row.get("servings", "")
            has_chocochip = 1 if row.get("has_chocochip", "").lower() == "true" else 0
            features = row.get("visual_features", "")
            img_path = normalize_image_path(row.get("image_path", ""))
            prep_time = row.get("prep_time", "3-4 hours")
            confirmation = row.get("order_confirmation", "")
            desc = row.get("description", "")
            price = float(row["price_inr"]) if row.get("price_inr") and row["price_inr"].strip() else 0.0
            p_type = row.get("pricing_type", "")
            channel = row.get("ordering_channel", "")
            options = row.get("customization_options", "")
            p_status = row.get("price_status", "")

            ibm_db.execute(stmt, (cid, sku, d_code, name, cat, flavor, sub_cat, variants, service, weight, servings, has_chocochip, features, img_path, prep_time, confirmation, desc, price, p_type, channel, options, p_status))
            count += 1
    print(f"-> Ingested {count} Custom Designer Cakes.")

def ingest_party_accessories(conn):
    csv_path = os.path.join(DATA_DIR, "bakebox_party_and_accessories_rows (1).csv")
    print(f"Ingesting Party & Accessories from {csv_path}...")
    sql = """
        INSERT INTO BB_PARTY_ACCESSORIES
        (sku_id, item_name, category, sub_category, pack_size_or_servings, price_inr, is_vegetarian, image_path, visual_features, description, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """
    stmt = ibm_db.prepare(conn, sql)
    count = 0
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row["sku_id"]
            name = row["item_name"]
            cat = row.get("category", "")
            sub_cat = row.get("sub_category", "")
            servings = row.get("pack_size_or_servings", "")
            price = float(row["price_inr"]) if row.get("price_inr") else 0.0
            is_veg = 1 if row.get("is_vegetarian", "true").lower() == "true" else 0
            img_path = normalize_image_path(row.get("image_path", ""))
            features = row.get("visual_features", "")
            desc = row.get("description", "")

            ibm_db.execute(stmt, (sku, name, cat, sub_cat, servings, price, is_veg, img_path, features, desc))
            count += 1
    print(f"-> Ingested {count} Party & Accessories items.")

def ingest_bakery_raw(conn):
    csv_path = os.path.join(DATA_DIR, "bakery_raw_rows (1).csv")
    print(f"Ingesting Bakery Raw & Patties from {csv_path}...")
    sql = """
        INSERT INTO BB_BAKERY_RAW
        (sku_id, item_name, category_section, shape, potato_mash_type, filling_technique, has_onion, has_paneer, has_egg, is_eggless, is_wholesale_eligible, shelf_life_hours, thermal_type, description, price_inr, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """
    stmt = ibm_db.prepare(conn, sql)
    count = 0
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row["sku_id"]
            name = row["item_name"]
            cat = row.get("category_section", "")
            shape = row.get("shape", "")
            mash = row.get("potato_mash_type", "")
            filling = row.get("filling_technique", "")
            has_onion = 1 if row.get("has_onion", "").lower() == "true" else 0
            has_paneer = 1 if row.get("has_paneer", "").lower() == "true" else 0
            has_egg = 1 if row.get("has_egg", "").lower() == "true" else 0
            is_eggless = 1 if row.get("is_eggless", "true").lower() == "true" else 0
            is_wholesale = 1 if row.get("is_wholesale_eligible", "").lower() == "true" else 0
            shelf = int(row["shelf_life_hours"]) if row.get("shelf_life_hours") else 24
            thermal = row.get("thermal_type", "OVEN_ITEM")
            desc = row.get("description", "")
            price = float(row["price_inr"]) if row.get("price_inr") else 15.0

            ibm_db.execute(stmt, (sku, name, cat, shape, mash, filling, has_onion, has_paneer, has_egg, is_eggless, is_wholesale, shelf, thermal, desc, price))
            count += 1
    print(f"-> Ingested {count} Bakery Raw items.")


def collect_rag_chunks():
    chunks = []

    # 1. Standard Cakes
    cakes_csv = os.path.join(DATA_DIR, "cakes_rows (6).csv")
    with open(cakes_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunk_text = row.get("rag_chunk") or (row.get("name") + " " + row.get("description", ""))
            meta = {
                "source": "CAKE",
                "sku_id": row["sku_id"],
                "name": row["name"],
                "flavor": row.get("flavor", ""),
                "category": row.get("category", ""),
                "price": float(row.get("price", 0)),
                "weight_kg": float(row.get("weight_kg", 0.5)),
                "available_base_variants": row.get("available_base_variants", ""),
                "image_path": normalize_image_path(row.get("image_path", "")),
                "prep_time": row.get("prep_time", "3-4 hours"),
                "chocochip": row.get("has_chocochip", "false")
            }
            chunks.append({
                "chunk_id": f"CAKE_{row['sku_id']}",
                "source_type": "CAKE",
                "sku_or_title": row["name"],
                "chunk_text": chunk_text,
                "metadata": meta
            })

    # 2. Custom Designer Cakes
    custom_csv = os.path.join(DATA_DIR, "custom_cakes_catalog_rows (1).csv")
    with open(custom_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunk_text = row.get("rag_chunk") or (row.get("name") + " " + row.get("description", ""))
            meta = {
                "source": "CUSTOM_CAKE",
                "sku_id": row["sku_id"],
                "name": row["name"],
                "flavor": row.get("flavor", ""),
                "category": row.get("category", "PREMIUM Custom Designer"),
                "price": float(row.get("price_inr") or 0.0),
                "weight_kg": float(row.get("weight_kg", 1.0)),
                "available_base_variants": row.get("available_base_variants", ""),
                "image_path": normalize_image_path(row.get("image_path", "")),
                "prep_time": row.get("prep_time", "3-4 hours"),
                "service_type": row.get("service_type", "1-on-1 Personal Baker Call & Customization Service"),
                "ordering_channel": row.get("ordering_channel", "WhatsApp/Phone consultation required")
            }
            chunks.append({
                "chunk_id": f"CUSTOM_{row['sku_id']}_{row['id']}",
                "source_type": "CUSTOM_CAKE",
                "sku_or_title": row["name"],
                "chunk_text": chunk_text,
                "metadata": meta
            })

    # 3. Party & Accessories
    party_csv = os.path.join(DATA_DIR, "bakebox_party_and_accessories_rows (1).csv")
    with open(party_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunk_text = row.get("rag_chunk") or (row.get("item_name") + " " + row.get("description", ""))
            meta = {
                "source": "PARTY_ACCESSORIES",
                "sku_id": row["sku_id"],
                "name": row["item_name"],
                "category": row.get("category", ""),
                "sub_category": row.get("sub_category", ""),
                "price": float(row.get("price_inr", 0)),
                "servings": row.get("pack_size_or_servings", ""),
                "is_vegetarian": row.get("is_vegetarian", "true"),
                "image_path": normalize_image_path(row.get("image_path", ""))
            }
            chunks.append({
                "chunk_id": f"PARTY_{row['sku_id']}",
                "source_type": "PARTY_ACCESSORIES",
                "sku_or_title": row["item_name"],
                "chunk_text": chunk_text,
                "metadata": meta
            })

    # 4. Bakery Raw (Patties)
    raw_csv = os.path.join(DATA_DIR, "bakery_raw_rows (1).csv")
    with open(raw_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunk_text = row.get("rag_chunk") or (row.get("item_name") + " " + row.get("description", ""))
            meta = {
                "source": "BAKERY_RAW",
                "sku_id": row["sku_id"],
                "name": row["item_name"],
                "shape": row.get("shape", ""),
                "price": float(row.get("price_inr", 15)),
                "shelf_life_hours": int(row.get("shelf_life_hours", 24)),
                "thermal_type": row.get("thermal_type", "OVEN_ITEM"),
                "reheating": "Dry tawa 2-3 mins (Never microwave)"
            }
            chunks.append({
                "chunk_id": f"RAW_{row['sku_id']}",
                "source_type": "BAKERY_RAW",
                "sku_or_title": row["item_name"],
                "chunk_text": chunk_text,
                "metadata": meta
            })

    # 5. Policy PDF Chunks
    pdf1_path = os.path.join(DATA_DIR, "policy andapp agreemnet.pdf")
    if os.path.exists(pdf1_path):
        reader = pypdf.PdfReader(pdf1_path)
        for idx, page in enumerate(reader.pages):
            text = page.extract_text().strip()
            if text:
                meta = {
                    "source": "POLICY_PDF",
                    "doc_title": "BAKEBOX App Terms of Use, User Privileges & Privacy Policy",
                    "page": idx + 1
                }
                chunks.append({
                    "chunk_id": f"POLICY_P{idx+1}",
                    "source_type": "POLICY_PDF",
                    "sku_or_title": f"BAKEBOX App Policy (Page {idx+1})",
                    "chunk_text": f"Document: BAKEBOX Policy & App Agreement | Page {idx+1}\n{text}",
                    "metadata": meta
                })

    # 6. Store Working PDF Chunks
    pdf2_path = os.path.join(DATA_DIR, "user agreement and store working.pdf")
    if os.path.exists(pdf2_path):
        reader = pypdf.PdfReader(pdf2_path)
        for idx, page in enumerate(reader.pages):
            text = page.extract_text().strip()
            if text:
                meta = {
                    "source": "STORE_WORKING_PDF",
                    "doc_title": "BAKEBOX Official User Agreement, Store Policy & Service Guarantee",
                    "partner": "Shri Ram Bakery, Mathura",
                    "page": idx + 1
                }
                chunks.append({
                    "chunk_id": f"STORE_P{idx+1}",
                    "source_type": "STORE_WORKING_PDF",
                    "sku_or_title": f"Store Working Agreement (Page {idx+1})",
                    "chunk_text": f"Document: Shri Ram Bakery Store Policy & Working Agreement | Page {idx+1}\n{text}",
                    "metadata": meta
                })

    return chunks


def build_and_ingest_rag_chunks(conn):
    chunks = collect_rag_chunks()
    print(f"Total collected RAG Chunks: {len(chunks)}")
    print("Loading HuggingFace dense embedding model: BAAI/bge-small-en-v1.5...")
    embed_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    
    texts = [c["chunk_text"] for c in chunks]
    print(f"Generating dense embeddings for {len(texts)} chunks...")
    embeddings = list(embed_model.embed(texts, batch_size=64))
    print(f"Generated {len(embeddings)} dense embeddings (dim = {len(embeddings[0])})")

    sql = """
        INSERT INTO BB_RAG_CHUNKS 
        (chunk_id, source_type, sku_or_title, chunk_text, metadata_json, embedding)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    stmt = ibm_db.prepare(conn, sql)
    print("Writing RAG chunks with dense embeddings into IBM Db2 BB_RAG_CHUNKS table...")
    count = 0
    for chunk, emb in zip(chunks, embeddings):
        c_id = chunk["chunk_id"]
        s_type = chunk["source_type"]
        title = chunk["sku_or_title"]
        txt = chunk["chunk_text"]
        m_json = json.dumps(chunk["metadata"])
        emb_json = json.dumps(emb.tolist())

        ibm_db.execute(stmt, (c_id, s_type, title, txt, m_json, emb_json))
        count += 1
        if count % 100 == 0:
            print(f"  -> Inserted {count}/{len(chunks)} chunks...")
            
    print(f"-> Successfully stored all {count} RAG chunks and dense embeddings into IBM Db2!")


def main():
    print("Starting BAKEBOX Full Ingestion Pipeline...")
    conn = get_db_conn()
    
    # Clean previous records if any to avoid duplication
    for tbl in ["BB_RAG_CHUNKS", "BB_CAKES", "BB_CUSTOM_CAKES", "BB_PARTY_ACCESSORIES", "BB_BAKERY_RAW", "BB_ADMIN_OPERATORS"]:
        try:
            ibm_db.exec_immediate(conn, f"DELETE FROM {tbl}")
        except Exception:
            pass

    ingest_admin_operators(conn)
    seed_users(conn)
    ingest_cakes(conn)
    ingest_custom_cakes(conn)
    ingest_party_accessories(conn)
    ingest_bakery_raw(conn)
    build_and_ingest_rag_chunks(conn)

    ibm_db.close(conn)
    print("=== Ingestion and RAG Chunks Pipeline Finished Successfully ===")


if __name__ == "__main__":
    main()
