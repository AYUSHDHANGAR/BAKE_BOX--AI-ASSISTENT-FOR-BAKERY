"""
BAKEBOX CHOCO AI Assistant Engine.
Powered by LlamaIndex BaseRetriever, Hybrid RAG (BAAI/bge-small-en-v1.5 + TF-IDF Sparse + RRF + Cross-Encoder Reranker),
Corrective RAG (CRAG) evaluation, Gemini API (gemini-flash-latest), and isolated IBM Db2 conversation buffers.
"""
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from google import genai
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, TextNode

import app.config
from app.db import get_db, query_all, query_one, execute_dml
from app.rag.embeddings import DenseEmbeddingEngine, SparseTFIDFEngine
from app.rag.reranker import CrossEncoderReranker
from app.rag.crag import CorrectiveRAGEvaluator
from app.rag.self_evaluator import SelfRAGEvaluator

def get_gemini_api_key():
    return os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API") or ""

CHOCO_SYSTEM_PROMPT = """You are CHOCO, the beloved autonomous master baker AI assistant of Shri Ram Baker's BAKEBOX in Mathura.

STYLE & TONE GUIDELINES:
1. Strict Hinglish Conversational Style: Warm, friendly, culturally rooted, polite and respectful. Use phrases like:
   - "Ji bilkul, hamare paas..."
   - "Radhe Radhe ji! Shri Ram Baker's BAKEBOX mein aapka swagat hai!"
   - "Aapke celebration ko super special banane ke liye..."
   - "Bilkul fresh bake karke denge aapko!"
2. Authenticity & Store Policies (from Shri Ram Bakery Mathura):
   - Locations: Branch 1: Bhagel Chaupal, Khatoti Kua (Mathura) | Branch 2: Gausna (Mathura).
   - Standard Cakes Baking Time: 3-4 hours fresh baking wait time after order placement.
   - Custom Designer Cakes (Barbie Doll, Tiered, Princess, etc.): We provide a dedicated 1-on-1 personal baker consultation over call/WhatsApp. Customer requests desired weight in kg and custom design; our master baker confirms feasibility, exact custom quote, and delivery details. Never invent or guess arbitrary prices for custom non-standard weight designs.
   - Cake Bases: Khoaa (Eggless), Pure Veg Eggless, Chocolate Eggless, and Egg. Always highlight 100% pure vegetarian / eggless options proudly.
   - Bakery Snacks & Patties: Oven items (Aloo, Paneer, Mayo, Tandoori). Warm reminder: Reheat on dry tawa for 2-3 mins, NEVER microwave!
3. Dynamic UI Output & Recommendation Cards:
   Whenever the user asks for suggestions, recommendations, designs, flavors, or cake options (e.g. 'show me red velvet cake', 'mujhe black forest cake chahiye', 'kuch cake suggest karo', 'pineapple cake dikhao', etc.):
   - You MUST include EXACTLY 3 distinct cake options in the ```json_cards``` array matching the user's requested flavor/theme directly from the retrieved context.
   - Format your output with the special JSON block at the very end:
   ```json_cards
   [
     {
       "sku_id": "BB-BLK-01-05kg",
       "name": "Black Forest Classic Cherry Gateau",
       "flavor": "Black Forest",
       "category": "ACE",
       "weight_kg": 0.5,
       "price": 249.0,
       "image_url": "/catalog_images/CAKES_BRANDED/ACE/Black Forest/BAKEBOX_ACE_BlackForest_01.jpg",
       "available_base_variants": "Khoaa (Eggless), Eggless, Chocolate Eggless, Egg",
       "is_custom": false
     },
     {
       "sku_id": "BB-BLK-02-05kg",
       "name": "Black Forest Lattice Grid",
       "flavor": "Black Forest",
       "category": "ACE",
       "weight_kg": 0.5,
       "price": 249.0,
       "image_url": "/catalog_images/CAKES_BRANDED/ACE/Black Forest/BAKEBOX_ACE_BlackForest_02.jpg",
       "available_base_variants": "Khoaa (Eggless), Eggless, Chocolate Eggless, Egg",
       "is_custom": false
     },
     {
       "sku_id": "BB-BLK-03-05kg",
       "name": "Black Forest Cherry Drizzle",
       "flavor": "Black Forest",
       "category": "ACE",
       "weight_kg": 0.5,
       "price": 249.0,
       "image_url": "/catalog_images/CAKES_BRANDED/ACE/Black Forest/BAKEBOX_ACE_BlackForest_03.jpg",
       "available_base_variants": "Khoaa (Eggless), Eggless, Chocolate Eggless, Egg",
       "is_custom": false
     }
   ]
   ```
   - Always ensure EXACTLY 3 matching cakes are provided in the json_cards array when recommending.
   - If the user is NOT asking for recommendations (e.g. asking for order status, heating rules on dry tawa, store branch hours, general greeting), output ```json_cards []```.
"""

class BakeboxHybridRetriever(BaseRetriever):
    """
    Custom LlamaIndex Retriever implementing Hybrid Dense + Sparse RRF Retrieval.
    """
    def __init__(self, dense_engine, sparse_engine, reranker, crag_evaluator, chunks_dict, dense_matrix, doc_ids):
        super().__init__()
        self.dense_engine = dense_engine
        self.sparse_engine = sparse_engine
        self.reranker = reranker
        self.crag_evaluator = crag_evaluator
        self.chunks_dict = chunks_dict
        self.dense_matrix = dense_matrix
        self.doc_ids = doc_ids

    def _retrieve(self, query_bundle) -> list[NodeWithScore]:
        query_str = query_bundle.query_str
        return self.hybrid_search(query_str)

    def hybrid_search(self, query: str, top_dense: int = 30, top_sparse: int = 30, top_k: int = 10) -> list[NodeWithScore]:
        # 1. Dense retrieval
        q_emb = self.dense_engine.embed_query(query).reshape(1, -1)
        dense_sims = cosine_similarity(q_emb, self.dense_matrix)[0]
        top_dense_indices = np.argsort(dense_sims)[::-1][:top_dense]

        # 2. Sparse retrieval
        sparse_results = self.sparse_engine.search(query, top_k=top_sparse)
        sparse_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(sparse_results)}

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF_score(d) = sum(1 / (60 + rank))
        rrf_scores = {}
        for rank, idx in enumerate(top_dense_indices):
            doc_id = self.doc_ids[idx]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (60.0 + (rank + 1)))

        for doc_id, s_rank in sparse_ranks.items():
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (60.0 + s_rank))

        # Sort candidate documents by RRF score
        sorted_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:15]
        candidate_docs = []
        for doc_id, rrf_s in sorted_candidates:
            c = self.chunks_dict.get(doc_id)
            if c:
                candidate_docs.append({
                    "id": doc_id,
                    "text": c["chunk_text"],
                    "metadata": c["metadata"],
                    "rrf_score": rrf_s
                })

        # 4. Cross-Encoder Reranking
        reranked_docs = self.reranker.rerank(query, candidate_docs, top_k=top_k)

        # 5. Corrective RAG (CRAG) Evaluation
        crag_status, final_docs = self.crag_evaluator.evaluate_retrieval(query, reranked_docs)
        if crag_status in ["AMBIGUOUS", "INCORRECT"]:
            transformed_q = self.crag_evaluator.transform_query(query)
            if transformed_q != query:
                # Secondary corrective search
                extra_sparse = self.sparse_engine.search(transformed_q, top_k=5)
                for doc_id, _ in extra_sparse:
                    if doc_id in self.chunks_dict and all(d["id"] != doc_id for d in final_docs):
                        c = self.chunks_dict[doc_id]
                        final_docs.append({
                            "id": doc_id,
                            "text": c["chunk_text"],
                            "metadata": c["metadata"],
                            "rerank_score": 0.2
                        })

        # Format into LlamaIndex NodeWithScore
        nodes = []
        for doc in final_docs[:top_k]:
            node = TextNode(
                text=doc["text"],
                id_=doc["id"],
                metadata=doc.get("metadata", {})
            )
            nodes.append(NodeWithScore(node=node, score=doc.get("rerank_score", 0.0)))
        return nodes


class ChocoAIEngine:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        print("Initializing CHOCO AI Engine with Gemini API & IBM Db2...")
        self.dense_engine = DenseEmbeddingEngine.get_instance()
        self.sparse_engine = SparseTFIDFEngine()
        self.reranker = CrossEncoderReranker.get_instance()
        self.crag_evaluator = CorrectiveRAGEvaluator()
        self.self_evaluator = SelfRAGEvaluator()
        
        # Initialize Gemini Client with ultra-fast model (1.2s latency)
        api_key = get_gemini_api_key()
        if api_key:
            self.gemini_client = genai.Client(api_key=api_key)
        else:
            self.gemini_client = genai.Client()
        self.model_name = "gemini-3.5-flash-lite"

        # Load chunks from IBM Db2
        self.chunks_dict = {}
        self.doc_ids = []
        dense_vectors = []
        corpus_texts = []

        with get_db() as conn:
            rows = query_all(conn, "SELECT chunk_id, source_type, sku_or_title, chunk_text, metadata_json, embedding FROM BB_RAG_CHUNKS")
            print(f"Loaded {len(rows)} chunks from IBM Db2 BB_RAG_CHUNKS.")
            for r in rows:
                c_id = r["CHUNK_ID"]
                txt = r["CHUNK_TEXT"]
                meta = json.loads(r["METADATA_JSON"]) if r["METADATA_JSON"] else {}
                emb = json.loads(r["EMBEDDING"]) if r["EMBEDDING"] else []

                self.chunks_dict[c_id] = {
                    "source_type": r["SOURCE_TYPE"],
                    "sku_or_title": r["SKU_OR_TITLE"],
                    "chunk_text": txt,
                    "metadata": meta
                }
                self.doc_ids.append(c_id)
                dense_vectors.append(emb)
                corpus_texts.append(txt)

        self.dense_matrix = np.array(dense_vectors, dtype=np.float32)
        print("Fitting Lexical TF-IDF Vectorizer across IBM Db2 chunks...")
        self.sparse_engine.fit(self.doc_ids, corpus_texts)

        # Build LlamaIndex Hybrid Retriever
        self.retriever = BakeboxHybridRetriever(
            dense_engine=self.dense_engine,
            sparse_engine=self.sparse_engine,
            reranker=self.reranker,
            crag_evaluator=self.crag_evaluator,
            chunks_dict=self.chunks_dict,
            dense_matrix=self.dense_matrix,
            doc_ids=self.doc_ids
        )
        print("CHOCO AI Engine & LlamaIndex Retriever fully ready!")

    def get_user_buffer(self, user_id: int, session_id: str, limit: int = 10) -> list[dict]:
        """Load isolated conversation buffer from IBM Db2 for a specific user and session."""
        with get_db() as conn:
            sql = """
                SELECT role, content, ui_cards_json, crag_status, created_at 
                FROM BB_USER_CONVERSATION_BUFFER 
                WHERE user_id = ? AND session_id = ? 
                ORDER BY buffer_id ASC
            """
            rows = query_all(conn, sql, (user_id, session_id))
            return rows[-limit:] if rows else []

    def save_buffer_message(self, user_id: int, session_id: str, role: str, content: str, ui_cards: list = None, crag_status: str = "CONFIDENT"):
        """Save message to isolated user conversation buffer in IBM Db2."""
        ui_json = json.dumps(ui_cards) if ui_cards else "[]"
        with get_db() as conn:
            sql = """
                INSERT INTO BB_USER_CONVERSATION_BUFFER 
                (user_id, session_id, role, content, ui_cards_json, crag_status) 
                VALUES (?, ?, ?, ?, ?, ?)
            """
            execute_dml(conn, sql, (user_id, session_id, role, content, ui_json, crag_status))

    def clear_user_buffer(self, user_id: int, session_id: str):
        """Clear conversation buffer for a user session."""
        with get_db() as conn:
            sql = "DELETE FROM BB_USER_CONVERSATION_BUFFER WHERE user_id = ? AND session_id = ?"
            execute_dml(conn, sql, (user_id, session_id))

    def lookup_user_orders(self, user_id: int, query: str) -> tuple[dict | None, list[dict]]:
        """Search for customer's live orders in IBM Db2. Extracts order ID or phone if present, or checks recent orders."""
        import re
        order_id_match = re.search(r'(?:order\s*#?|#)(\d{4,})', query, re.I)
        if not order_id_match:
            order_id_match = re.search(r'\b(10\d{2})\b', query)
        phone_match = re.search(r'\b(\d{10})\b', query)

        with get_db() as conn:
            order = None
            if order_id_match:
                oid = int(order_id_match.group(1))
                order = query_one(conn, "SELECT * FROM BB_ORDERS WHERE order_id = ?", (oid,))
            elif phone_match:
                phone = phone_match.group(1)
                order = query_one(conn, "SELECT * FROM BB_ORDERS WHERE customer_phone LIKE ? ORDER BY order_id DESC", (f"%{phone}%",))
            elif user_id:
                order = query_one(conn, "SELECT * FROM BB_ORDERS WHERE user_id = ? ORDER BY order_id DESC", (user_id,))

            items = []
            if order and "ORDER_ID" in order:
                items = query_all(conn, "SELECT * FROM BB_ORDER_ITEMS WHERE order_id = ?", (order["ORDER_ID"],))
            return order, items

    def find_matching_3_cakes(self, query: str, existing_cards: list, candidate_cards: list) -> list[dict]:
        """
        Guarantees that exactly 3 distinct cakes matching the customer's query are returned.
        1. Keeps valid cards provided by Gemini.
        2. Fills from candidate_cards from hybrid retrieval.
        3. Fills from IBM Db2 chunks matching the queried flavor/theme.
        """
        import re
        q_lower = query.lower()
        selected = list(existing_cards)
        seen_skus = {c.get("sku_id") for c in selected if c.get("sku_id")}
        
        # 1. Fill from candidate_cards from hybrid retrieval
        for c in candidate_cards:
            if len(selected) >= 3:
                break
            sku = c.get("sku_id")
            if sku and sku not in seen_skus:
                selected.append(c)
                seen_skus.add(sku)
                
        # 2. If still < 3, detect flavor or theme from query
        if len(selected) < 3:
            known_flavors = [
                "red velvet", "black forest", "white forest", "pineapple", "chocolate", 
                "truffle", "strawberry", "butterscotch", "vanilla", "mango", "blueberry", 
                "rasmalai", "gulab jamun", "kitkat", "oreo", "hazelnut", "fruit", "caramel",
                "barbie", "doll", "princess", "tier", "heart"
            ]
            matched_flavor = None
            for f in known_flavors:
                if f in q_lower:
                    matched_flavor = f
                    break
                    
            if matched_flavor:
                for chunk_id, c in self.chunks_dict.items():
                    if len(selected) >= 3:
                        break
                    if c.get("source_type") not in ("CAKE", "CUSTOM_CAKE"):
                        continue
                    meta = c.get("metadata", {})
                    sku = meta.get("sku_id")
                    if not sku or sku in seen_skus:
                        continue
                    f_name = (meta.get("flavor") or "").lower()
                    name = (meta.get("name") or "").lower()
                    if matched_flavor in f_name or matched_flavor in name:
                        selected.append({
                            "sku_id": sku,
                            "name": meta.get("name"),
                            "flavor": meta.get("flavor", ""),
                            "category": meta.get("category", "BAKEBOX"),
                            "weight_kg": meta.get("weight_kg", 0.5),
                            "price": float(meta.get("price", 249.0)),
                            "image_url": meta.get("image_path", ""),
                            "available_base_variants": meta.get("available_base_variants", "Khoaa (Eggless), Veg Eggless, Egg"),
                            "is_custom": c.get("source_type") == "CUSTOM_CAKE"
                        })
                        seen_skus.add(sku)

        # 3. If still < 3, match by query keywords
        if len(selected) < 3:
            keywords = [w for w in re.findall(r'\w+', q_lower) if len(w) > 3 and w not in ["cake", "show", "batao", "chahiye", "dikhao", "some", "mujhe", "kripya", "recommend", "suggest", "options"]]
            for chunk_id, c in self.chunks_dict.items():
                if len(selected) >= 3:
                    break
                if c.get("source_type") not in ("CAKE", "CUSTOM_CAKE"):
                    continue
                meta = c.get("metadata", {})
                sku = meta.get("sku_id")
                if not sku or sku in seen_skus:
                    continue
                text = (meta.get("name", "") + " " + meta.get("flavor", "") + " " + meta.get("description", "")).lower()
                if any(k in text for k in keywords):
                    selected.append({
                        "sku_id": sku,
                        "name": meta.get("name"),
                        "flavor": meta.get("flavor", ""),
                        "category": meta.get("category", "BAKEBOX"),
                        "weight_kg": meta.get("weight_kg", 0.5),
                        "price": float(meta.get("price", 249.0)),
                        "image_url": meta.get("image_path", ""),
                        "available_base_variants": meta.get("available_base_variants", "Khoaa (Eggless), Veg Eggless, Egg"),
                        "is_custom": c.get("source_type") == "CUSTOM_CAKE"
                    })
                    seen_skus.add(sku)

        # 4. Fallback to top cakes from chunks_dict if still < 3
        if len(selected) < 3:
            for chunk_id, c in self.chunks_dict.items():
                if len(selected) >= 3:
                    break
                if c.get("source_type") not in ("CAKE", "CUSTOM_CAKE"):
                    continue
                meta = c.get("metadata", {})
                sku = meta.get("sku_id")
                if sku and sku not in seen_skus:
                    selected.append({
                        "sku_id": sku,
                        "name": meta.get("name"),
                        "flavor": meta.get("flavor", ""),
                        "category": meta.get("category", "BAKEBOX"),
                        "weight_kg": meta.get("weight_kg", 0.5),
                        "price": float(meta.get("price", 249.0)),
                        "image_url": meta.get("image_path", ""),
                        "available_base_variants": meta.get("available_base_variants", "Khoaa (Eggless), Veg Eggless, Egg"),
                        "is_custom": c.get("source_type") == "CUSTOM_CAKE"
                    })
                    seen_skus.add(sku)

        return selected[:3]

    def chat(self, user_id: int, session_id: str, user_message: str) -> dict:
        """
        Full Execution Pipeline:
        1. Retrieve isolated conversation buffer history from IBM Db2.
        2. Execute LlamaIndex Hybrid Retrieval (BAAI/bge-small-en-v1.5 + TF-IDF Sparse + RRF).
        3. Cross-Encoder Rerank candidate passages.
        4. Corrective RAG (CRAG) evaluation & query adaptation.
        5. Build synthesized context.
        6. Generate Hinglish response with Gemini API.
        7. Extract UI cards and update isolated conversation buffer in IBM Db2.
        """
        # Save user message in IBM Db2 buffer
        self.save_buffer_message(user_id, session_id, "user", user_message)

        # Check if query is about order status / tracking
        order_keywords = ["order", "status", "mera order", "order id", "track", "delivery", "kahan pahuncha", "placed one order", "placed order", "order status"]
        is_order_query = any(k in user_message.lower() for k in order_keywords)
        
        live_order, order_items = None, []
        if is_order_query:
            live_order, order_items = self.lookup_user_orders(user_id, user_message)
            if not live_order:
                # User hasn't placed an order or hasn't provided order id
                order_reply = (
                    "Radhe Radhe ji! 🙏\n\n"
                    "Ji bilkul, main abhi aapke order ka live status check kar deta hoon!\n\n"
                    "Kya aap kripya apna **Order ID** ya **registered mobile number** share kar sakte hain?\n\n"
                    "Aapko ek chhota sa idea de doon:\n"
                    "- Agar aapka standard **Fresh Live Cake** hai, toh use fresh soak, decorate aur cold-set hone mein lagbhag **3 se 4 ghante (hours)** lagte hain taaki delivery ke dauran cake bilkul safe aur fresh rahe.\n"
                    "- Agar aapne **Ready-to-Deliver** cake chuna tha, toh woh **1 se 2 ghante** mein dispatch ho jata hai.\n"
                    "- Hot oven snacks ya patties 45–60 minutes ke window mein deliver ho jate hain.\n\n"
                    "Aap apna Order ID bataiye, main turant hamare kitchen (Khatoti Kua / Gausna branch) se live update nikal kar aapko batata hoon ji! ✨"
                )
                self.save_buffer_message(user_id, session_id, "assistant", order_reply, ui_cards=[])
                return {
                    "reply": order_reply,
                    "ui_cards": [],
                    "retrieved_count": 0,
                    "self_eval": {"status": "ORDER_PROMPT_DELIVERED"}
                }

        order_context_str = ""
        if live_order:
            items_desc = ", ".join([f"{it['QUANTITY']}x {it['ITEM_NAME']} ({it.get('CAKE_WEIGHT', '')}, {it.get('CAKE_BASE', '')})" for it in order_items])
            order_context_str = f"""
LIVE CUSTOMER ORDER DATA DIRECTLY FROM IBM Db2 (Verified Ground Truth):
- Order ID: #{live_order['ORDER_ID']}
- Order Status: {live_order['ORDER_STATUS']}
- Customer Name: {live_order['CUSTOMER_NAME']}
- Customer Phone: {live_order['CUSTOMER_PHONE']}
- Total Amount: INR {live_order['TOTAL_AMOUNT']}
- Delivery Address: {live_order['DELIVERY_ADDRESS']}
- Items Ordered: {items_desc}
- Special Notes: {live_order.get('SPECIAL_NOTES', '')}
- Placed At: {live_order['CREATED_AT']}
Store Kitchen: Bhagel Chaupal, Khatoti Kua Branch (Fresh baking in progress for 3-4 hours fresh baking wait time)
"""

        # LlamaIndex Hybrid Retrieval with RRF and Cross-Encoder
        retrieved_nodes = self.retriever.retrieve(user_message)
        
        # Build context from retrieved nodes
        context_parts = []
        candidate_cards = []
        for n in retrieved_nodes:
            context_parts.append(f"[{n.node.id_} | Score: {n.score:.2f}]:\n{n.node.text}")
            meta = n.node.metadata
            if meta and meta.get("sku_id") and meta.get("image_path"):
                candidate_cards.append({
                    "sku_id": meta.get("sku_id"),
                    "name": meta.get("name"),
                    "flavor": meta.get("flavor", ""),
                    "category": meta.get("category", "BAKEBOX"),
                    "weight_kg": meta.get("weight_kg", 0.5),
                    "price": meta.get("price", 0.0),
                    "image_url": meta.get("image_path", ""),
                    "available_base_variants": meta.get("available_base_variants", ""),
                    "is_custom": meta.get("source") == "CUSTOM_CAKE"
                })

        context_text = "\n\n---\n\n".join(context_parts)

        # Load recent multi-turn conversation buffer for this isolated user
        recent_history = self.get_user_buffer(user_id, session_id, limit=6)
        history_formatted = ""
        for h in recent_history[:-1]:  # exclude the just-saved current query
            r_role = "Customer" if h["ROLE"].lower() == "user" else "CHOCO"
            history_formatted += f"{r_role}: {h['CONTENT']}\n"

        prompt = f"""System Instructions:
{CHOCO_SYSTEM_PROMPT}

{order_context_str if order_context_str else ""}

Recent Conversation History with this Customer:
{history_formatted if history_formatted else "New conversation session."}

Retrieved Knowledge Base Context (from Shri Ram Bakery Products, Store Working Agreements & Policy):
{context_text}

Customer's Current Query:
{user_message}

Please provide your helpful, polite Hinglish response following the CHOCO persona and include any relevant ````json_cards```` for cakes/products:"""

        # Generate response using Google Gemini with dynamic fallback across models
        candidate_models = [self.model_name, "gemini-3.8-flash", "gemini-flash-lite-latest", "gemini-3.5-flash", "gemini-flash-latest"]
        full_reply = ""
        for m in candidate_models:
            try:
                response = self.gemini_client.models.generate_content(
                    model=m,
                    contents=prompt
                )
                if response and response.text:
                    full_reply = response.text
                    break
            except Exception as e:
                print(f"[CHOCO Fallback] Model {m} encountered: {e}. Trying next available model...")
                continue

        if not full_reply:
            full_reply = f"Radhe Radhe ji! Shri Ram Baker's BAKEBOX mein aapka swagat hai. Aapke query ke anusaar hamare fresh baked cakes aur bakery details niche present kar rahe hain. Kripya inme se check karein!"

        # Extract JSON cards if present
        ui_cards = []
        clean_reply = full_reply
        if "```json_cards" in full_reply:
            parts = full_reply.split("```json_cards")
            clean_reply = parts[0].strip()
            rest = parts[1]
            if "```" in rest:
                json_str = rest.split("```")[0].strip()
                try:
                    ui_cards = json.loads(json_str)
                except Exception:
                    pass
        elif "```json" in full_reply and any(k in full_reply for k in ["sku_id", "price", "image_url"]):
            parts = full_reply.split("```json")
            clean_reply = parts[0].strip()
            rest = parts[1]
            if "```" in rest:
                json_str = rest.split("```")[0].strip()
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, list):
                        ui_cards = parsed
                    elif isinstance(parsed, dict) and "ui_cards" in parsed:
                        ui_cards = parsed["ui_cards"]
                except Exception:
                    pass

        # AI Tool Calling & Recommendation Intent Detection:
        # Structured product cards are generated ONLY when the user explicitly requests cake suggestions/recommendations
        rec_signals = ["show", "suggest", "recommend", "option", "design", "dikhao", "batao", "chahiye", "cake", "available", "flavor", "variety", "rate", "price", "pairing", "matching", "candle", "snack", "detail", "sku"]
        non_rec_signals = ["order status", "mera order", "kahan hai", "track", "placed one order", "placed order", "reheat", "microwave", "tawa", "branch location", "store time"]
        
        user_msg_lower = user_message.lower()
        is_asking_recommendation = any(s in user_msg_lower for s in rec_signals) and not (
            any(ns in user_msg_lower for ns in non_rec_signals) and not any(ex in user_msg_lower for ex in ["suggest", "recommend", "show me", "dikhao"])
        )

        if not is_asking_recommendation:
            # Strictly do not show suggestions for non-recommendation queries
            ui_cards = []
        else:
            # Always provide EXACTLY 3 matching cakes for the user's query
            ui_cards = self.find_matching_3_cakes(user_message, ui_cards, candidate_cards)

        # Normalize and verify all cake cards using SKU-ID against IBM Db2 ground truth
        verified_cards = []
        import urllib.parse
        for card in ui_cards:
            sku = card.get("sku_id")
            matched_chunk = self.chunks_dict.get(f"CAKE_{sku}") or self.chunks_dict.get(f"CUSTOM_{sku}") or \
                next((c for c in self.chunks_dict.values() if c.get("metadata", {}).get("sku_id") == sku), None)
            
            raw_img = card.get("image_url", "")
            if matched_chunk:
                m = matched_chunk.get("metadata", {})
                raw_img = m.get("image_path") or raw_img
                price = float(m.get("price") or card.get("price") or 249.0)
                name = m.get("name") or card.get("name")
                flavor = m.get("flavor") or card.get("flavor", "")
                cat = m.get("category") or card.get("category", "BAKEBOX")
                w = float(m.get("weight_kg") or card.get("weight_kg", 0.5) or 0.5)
                variants = m.get("available_base_variants", "Khoaa (Eggless), Veg Eggless, Egg")
                is_custom = m.get("source") == "CUSTOM_CAKE"
            else:
                price = float(card.get("price") or 249.0)
                name = card.get("name", "Special Cake")
                flavor = card.get("flavor", "")
                cat = card.get("category", "BAKEBOX")
                w = float(card.get("weight_kg", 0.5) or 0.5)
                variants = card.get("available_base_variants", "Khoaa (Eggless), Veg Eggless, Egg")
                is_custom = card.get("is_custom", False)

            if raw_img:
                decoded = urllib.parse.unquote(raw_img)
                if "BAKEBOX_CATALOG/" in decoded:
                    idx = decoded.find("BAKEBOX_CATALOG/")
                    rel_path = decoded[idx + len("BAKEBOX_CATALOG/"):].replace("\\", "/")
                    norm_img = f"/catalog_images/{rel_path}"
                elif not decoded.startswith("/catalog_images/") and not decoded.startswith("http"):
                    norm_img = f"/catalog_images/{raw_img.lstrip('/')}"
                else:
                    norm_img = raw_img
            else:
                norm_img = "/catalog_images/CAKES_BRANDED/ACE/Black Forest/BAKEBOX_ACE_BlackForest_01.jpg"

            verified_cards.append({
                "sku_id": sku or f"BB-GEN-{len(verified_cards)+1}",
                "name": name,
                "flavor": flavor,
                "category": cat,
                "weight_kg": w,
                "price": price,
                "image_url": norm_img,
                "available_base_variants": variants,
                "is_custom": is_custom
            })

        # Final guarantee: if asking recommendation, ensure exactly 3 cards
        if is_asking_recommendation and len(verified_cards) < 3:
            verified_cards = self.find_matching_3_cakes(user_message, verified_cards, candidate_cards)
            for c in verified_cards:
                if not c["image_url"].startswith("/catalog_images/") and not c["image_url"].startswith("http"):
                    c["image_url"] = f"/catalog_images/{c['image_url'].lstrip('/')}"

        ui_cards = verified_cards[:3] if is_asking_recommendation else []

        # Self-Evaluation & Fact Verification Check (Self-RAG)
        eval_result = self.self_evaluator.evaluate_and_correct(
            clean_reply, user_message, context_text, order_data=live_order
        )
        clean_reply = eval_result["corrected_reply"]

        # Save assistant response into IBM Db2 buffer
        self.save_buffer_message(user_id, session_id, "assistant", clean_reply, ui_cards=ui_cards, crag_status=eval_result.get("status", "VERIFIED"))

        return {
            "reply": clean_reply,
            "ui_cards": ui_cards,
            "retrieved_count": len(retrieved_nodes),
            "self_eval": eval_result
        }
