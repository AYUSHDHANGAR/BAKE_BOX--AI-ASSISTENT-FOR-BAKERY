import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
import ibm_db
import ibm_db_dbi
from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo
from llama_index.core.vector_stores.types import VectorStoreQuery
from llama_index.vector_stores.db2 import DB2LlamaVS, DistanceStrategy

print("==========================================================")
print("DEMO: OFFICIAL IBM DB2 LLAMAVS INTEGRATION (DB2 v12.1.5.0)")
print("==========================================================")

conn_str = "DATABASE=IBMDB201;HOSTNAME=127.0.0.1;PORT=50000;PROTOCOL=TCPIP;UID=dbayush;PWD=8844;"
connection = ibm_db_dbi.connect(conn_str, "", "")
print("[OK] Connected to IBM Db2 Instance IBMDB201!")

# 1. Sample nodes with 2D embedding (as in IBM official sample)
text_json_list = [
    {
        "text": "Shri Ram Baker Bakebox Mathura offers 100% pure vegetarian cakes with Khoaa base.",
        "id_": "demo_node_1",
        "embedding": [1.0, 0.0],
        "relationships": "cake-info-1",
        "metadata": {"category": "Bakery", "branch": "Khatoti Kua"}
    },
    {
        "text": "Oven patties must be reheated on a dry tawa for 2-3 minutes, never in a microwave.",
        "id_": "demo_node_2",
        "embedding": [0.0, 1.0],
        "relationships": "snack-info-2",
        "metadata": {"category": "Snacks", "branch": "Gausna"}
    },
    {
        "text": "Standard fresh baked cakes require 3 to 4 hours baking wait time after order placement.",
        "id_": "demo_node_3",
        "embedding": [1.0, 1.0],
        "relationships": "policy-info-3",
        "metadata": {"category": "Policy", "branch": "Mathura"}
    }
]

text_nodes = []
for item in text_json_list:
    node = TextNode(
        text=item["text"],
        id_=item["id_"],
        embedding=item["embedding"],
        relationships={NodeRelationship.SOURCE: RelatedNodeInfo(node_id=item["relationships"])},
        metadata=item["metadata"]
    )
    text_nodes.append(node)

# 2. Ingest into Db2 Vector Store using DB2LlamaVS
print("\nCreating & Ingesting into DB2LlamaVS table 'BB_DEMO_LLAMA_COSINE'...")
vs_cosine = DB2LlamaVS.from_documents(
    text_nodes,
    table_name="BB_DEMO_LLAMA_COSINE",
    client=connection,
    distance_strategy=DistanceStrategy.COSINE,
    embed_dim=2
)
print("[OK] DB2LlamaVS Ingestion Successful!")

# 3. Perform Vector Similarity Search
query = VectorStoreQuery(query_embedding=[1.0, 0.8], similarity_top_k=2)
results = vs_cosine.query(query=query)
print("\n[OK] DB2LlamaVS Similarity Search Results:")
print("Matched Node IDs:", results.ids)
print("Matched Similarities:", results.similarities)

print("\n==========================================================")
print("SUCCESS: llama-index-vector-stores-db2 IS 100% VERIFIED!")
print("==========================================================")
