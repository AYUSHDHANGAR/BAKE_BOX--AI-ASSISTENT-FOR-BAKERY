import os
import sys
import json
import csv
import pypdf
import ibm_db
from fastembed import TextEmbedding

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.db import get_db, execute_dml

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "IBM_RAG_DATA tables & pdf"))

def normalize_image_path(path_str):
    if not path_str:
        return ""
    if "BAKEBOX_CATALOG/" in path_str:
        idx = path_str.find("BAKEBOX_CATALOG/")
        rel = path_str[idx + len("BAKEBOX_CATALOG/"):].replace("\\", "/")
        return f"/catalog_images/{rel}"
    if not path_str.startswith("/catalog_images/") and not path_str.startswith("http"):
        return f"/catalog_images/{path_str.lstrip('/')}"
    return path_str

def chunk_text_fixed_words(text: str, target_size: int = 75, min_words: int = 50, overlap: int = 15) -> list[str]:
    """Chunk text into fixed 50-100 words chunks as guided."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + target_size]
        if len(chunk_words) >= min_words or not chunks:
            chunks.append(" ".join(chunk_words))
        elif chunks:
            chunks[-1] += " " + " ".join(chunk_words)
        i += (target_size - overlap)
    return chunks

def build_all_chunks():
    chunks = []
    print("Collecting structured table nodes as individual chunks...")

    # 1. Standard Cakes table nodes
    cakes_csv = os.path.join(DATA_DIR, "cakes_rows (6).csv")
    with open(cakes_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunk_text = (
                f"Cake Product: {row['name']} | SKU: {row['sku_id']} | Design Code: {row.get('design_code', '')} | "
                f"Category: {row.get('category', '')} | Flavor: {row.get('flavor', '')} | "
                f"Weight: {row.get('weight_kg', '0.5')}kg | Price: INR {row.get('price', '249')} | "
                f"Servings: {row.get('servings', '4-6')} | Base Variants: {row.get('available_base_variants', 'Khoaa Eggless, Veg Eggless, Chocolate Eggless, Egg')} | "
                f"Prep Baking Time: {row.get('prep_time', '3-4 hours fresh baking')} | Features: {row.get('visual_features', '')} | "
                f"Description: {row.get('description', '')}"
            )
            meta = {
                "source": "STANDARD_CAKE",
                "sku_id": row["sku_id"],
                "name": row["name"],
                "flavor": row.get("flavor", ""),
                "category": row.get("category", ""),
                "price": float(row.get("price") or 249.0),
                "weight_kg": float(row.get("weight_kg", 0.5)),
                "available_base_variants": row.get("available_base_variants", ""),
                "image_path": normalize_image_path(row.get("image_path", "")),
                "prep_time": row.get("prep_time", "3-4 hours")
            }
            chunks.append({
                "chunk_id": f"CAKE_{row['sku_id']}",
                "source_type": "CAKE",
                "sku_or_title": row["name"],
                "chunk_text": chunk_text,
                "metadata": meta
            })
    print(f"-> Standard cake node chunks: {len(chunks)}")

    # 2. Custom Designer Cakes table nodes
    custom_csv = os.path.join(DATA_DIR, "custom_cakes_catalog_rows (1).csv")
    with open(custom_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunk_text = (
                f"Custom Designer Cake: {row['name']} | SKU: {row['sku_id']} | Category: {row.get('category', '')} | "
                f"Flavor: {row.get('flavor', '')} | Weight: {row.get('weight_kg', '1.0')}kg | "
                f"Price: INR {row.get('price_inr', 'Custom Quote')} | Service Type: 1-on-1 Personal Baker Call & Customization Service | "
                f"Ordering Channel: WhatsApp & Phone Consultation with Master Baker | "
                f"Available Base: {row.get('available_base_variants', '')} | Custom Options: {row.get('customization_options', '')} | "
                f"Description: {row.get('description', '')}"
            )
            meta = {
                "source": "CUSTOM_CAKE",
                "sku_id": row["sku_id"],
                "name": row["name"],
                "flavor": row.get("flavor", ""),
                "category": row.get("category", "Custom Designer"),
                "price": float(row.get("price_inr") or 0.0),
                "weight_kg": float(row.get("weight_kg", 1.0)),
                "available_base_variants": row.get("available_base_variants", ""),
                "image_path": normalize_image_path(row.get("image_path", "")),
                "service_type": "1-on-1 Personal Baker Call Consultation",
                "is_custom": True
            }
            chunks.append({
                "chunk_id": f"CUSTOM_{row['sku_id']}_{row['id']}",
                "source_type": "CUSTOM_CAKE",
                "sku_or_title": row["name"],
                "chunk_text": chunk_text,
                "metadata": meta
            })

    # 3. Party Accessories table nodes
    party_csv = os.path.join(DATA_DIR, "bakebox_party_and_accessories_rows (1).csv")
    with open(party_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunk_text = (
                f"Party Accessory: {row['item_name']} | SKU: {row['sku_id']} | Category: {row.get('category', '')} | "
                f"Sub-category: {row.get('sub_category', '')} | Price: INR {row.get('price_inr', '49')} | "
                f"Pack Size / Servings: {row.get('pack_size_or_servings', '')} | Description: {row.get('description', '')}"
            )
            meta = {
                "source": "PARTY_ACCESSORIES",
                "sku_id": row["sku_id"],
                "name": row["item_name"],
                "price": float(row.get("price_inr", 49)),
                "image_path": normalize_image_path(row.get("image_path", ""))
            }
            chunks.append({
                "chunk_id": f"PARTY_{row['sku_id']}",
                "source_type": "PARTY_ACCESSORIES",
                "sku_or_title": row["item_name"],
                "chunk_text": chunk_text,
                "metadata": meta
            })

    # 4. Bakery Raw / Oven Patties table nodes
    raw_csv = os.path.join(DATA_DIR, "bakery_raw_rows (1).csv")
    with open(raw_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunk_text = (
                f"Bakery Hot Snack / Oven Patty: {row['item_name']} | SKU: {row['sku_id']} | "
                f"Shape: {row.get('shape', '')} | Has Paneer: {row.get('has_paneer', '')} | Has Onion: {row.get('has_onion', '')} | "
                f"Price: INR {row.get('price_inr', '20')} | Thermal Type: Oven Item | "
                f"Shelf Life: {row.get('shelf_life_hours', '24')} hours | Reheating Guideline: Heat on dry tawa for 2-3 mins (Never microwave!) | "
                f"Description: {row.get('description', '')}"
            )
            meta = {
                "source": "BAKERY_RAW",
                "sku_id": row["sku_id"],
                "name": row["item_name"],
                "price": float(row.get("price_inr", 20)),
                "reheating": "Dry tawa 2-3 mins (Never microwave)"
            }
            chunks.append({
                "chunk_id": f"RAW_{row['sku_id']}",
                "source_type": "BAKERY_RAW",
                "sku_or_title": row["item_name"],
                "chunk_text": chunk_text,
                "metadata": meta
            })

    # 5. Policy PDF (Fixed 50-100 words chunking)
    pdf1_path = os.path.join(DATA_DIR, "policy andapp agreemnet.pdf")
    if os.path.exists(pdf1_path):
        reader = pypdf.PdfReader(pdf1_path)
        full_text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                full_text += " " + t
        pdf_chunks = chunk_text_fixed_words(full_text, target_size=75, min_words=50, overlap=15)
        print(f"-> Policy PDF chunked into {len(pdf_chunks)} fixed 50-100 word chunks.")
        for idx, c_text in enumerate(pdf_chunks, 1):
            chunks.append({
                "chunk_id": f"POLICY_FIXED_CHUNK_{idx}",
                "source_type": "POLICY_PDF",
                "sku_or_title": f"App Policy & Terms (Section {idx})",
                "chunk_text": f"BAKEBOX App Terms & Privacy Policy (Chunk {idx}, ~75 words):\n{c_text}",
                "metadata": {
                    "source": "POLICY_PDF",
                    "doc_title": "BAKEBOX App Policy",
                    "chunk_idx": idx,
                    "word_count": len(c_text.split())
                }
            })

    # 6. Store Working PDF (Fixed 50-100 words chunking)
    pdf2_path = os.path.join(DATA_DIR, "user agreement and store working.pdf")
    if os.path.exists(pdf2_path):
        reader = pypdf.PdfReader(pdf2_path)
        full_text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                full_text += " " + t
        store_chunks = chunk_text_fixed_words(full_text, target_size=75, min_words=50, overlap=15)
        print(f"-> Store Working PDF chunked into {len(store_chunks)} fixed 50-100 word chunks.")
        for idx, c_text in enumerate(store_chunks, 1):
            chunks.append({
                "chunk_id": f"STORE_FIXED_CHUNK_{idx}",
                "source_type": "STORE_WORKING_PDF",
                "sku_or_title": f"Shri Ram Bakery Store Working (Section {idx})",
                "chunk_text": f"Shri Ram Bakery Store Working Agreement & Mathura Guarantee (Chunk {idx}, ~75 words):\n{c_text}",
                "metadata": {
                    "source": "STORE_WORKING_PDF",
                    "doc_title": "Shri Ram Bakery Store Working Agreement",
                    "partner": "Shri Ram Bakery, Mathura",
                    "chunk_idx": idx,
                    "word_count": len(c_text.split())
                }
            })

    print(f"Total Combined Chunks for Vectorization: {len(chunks)}")
    return chunks

def ingest_chunks_into_ibmdb2():
    chunks = build_all_chunks()
    
    print("\nVectorizing all chunks using HuggingFace BAAI/bge-small-en-v1.5 (384-dim)...")
    embed_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    texts = [c["chunk_text"] for c in chunks]
    embeddings = list(embed_model.embed(texts, batch_size=128))
    print(f"Successfully generated {len(embeddings)} dense embeddings.")

    with get_db() as conn:
        print("Clearing previous BB_RAG_CHUNKS in IBMDB201...")
        execute_dml(conn, "DELETE FROM BB_RAG_CHUNKS")

        print("Ingesting fresh chunks & vectors into IBM Db2 BB_RAG_CHUNKS...")
        insert_sql = """
            INSERT INTO BB_RAG_CHUNKS 
            (chunk_id, source_type, sku_or_title, chunk_text, metadata_json, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor = conn.cursor()
        for idx, (c, emb) in enumerate(zip(chunks, embeddings)):
            emb_json = json.dumps(emb.tolist())
            meta_json = json.dumps(c["metadata"])
            cursor.execute(insert_sql, (
                c["chunk_id"],
                c["source_type"],
                c["sku_or_title"],
                c["chunk_text"],
                meta_json,
                emb_json
            ))
            if (idx + 1) % 100 == 0 or (idx + 1) == len(chunks):
                conn.commit()
                print(f"  Ingested {idx + 1}/{len(chunks)} chunks into IBM Db2...")

    print("ALL CHUNKS SUCCESSFULLY INGESTED INTO IBMDB201 BB_RAG_CHUNKS!")

if __name__ == "__main__":
    ingest_chunks_into_ibmdb2()
