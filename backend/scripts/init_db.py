"""
IBM Db2 Database Initializer for BAKEBOX platform.
Connects to IBMDB201 and creates all relational, RAG chunk, and conversation buffer tables.
"""
import ibm_db

DB2_CONN_STR = "DATABASE=IBMDB201;HOSTNAME=127.0.0.1;PORT=50000;PROTOCOL=TCPIP;UID=dbayush;PWD=8844;"

TABLES = [
    ("BB_USER_CONVERSATION_BUFFER", """
        CREATE TABLE BB_USER_CONVERSATION_BUFFER (
            buffer_id INT GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) PRIMARY KEY,
            user_id INT NOT NULL,
            session_id VARCHAR(100) NOT NULL,
            role VARCHAR(20) NOT NULL,
            content CLOB(32000) NOT NULL,
            ui_cards_json CLOB(32000),
            crag_status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT TIMESTAMP
        )
    """),
    ("BB_RAG_CHUNKS", """
        CREATE TABLE BB_RAG_CHUNKS (
            chunk_id VARCHAR(100) NOT NULL PRIMARY KEY,
            source_type VARCHAR(50) NOT NULL,
            sku_or_title VARCHAR(250) NOT NULL,
            chunk_text CLOB(32000) NOT NULL,
            metadata_json CLOB(32000) NOT NULL,
            embedding CLOB(64000) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT TIMESTAMP
        )
    """),
    ("BB_ORDER_ITEMS", """
        CREATE TABLE BB_ORDER_ITEMS (
            item_id INT GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) PRIMARY KEY,
            order_id INT NOT NULL,
            sku_id VARCHAR(50) NOT NULL,
            item_name VARCHAR(250) NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            unit_price DECIMAL(10,2) NOT NULL,
            cake_base VARCHAR(100),
            cake_weight VARCHAR(50),
            custom_message VARCHAR(200)
        )
    """),
    ("BB_ORDERS", """
        CREATE TABLE BB_ORDERS (
            order_id INT GENERATED ALWAYS AS IDENTITY (START WITH 1001 INCREMENT BY 1) PRIMARY KEY,
            user_id INT,
            customer_name VARCHAR(150) NOT NULL,
            customer_phone VARCHAR(30) NOT NULL,
            delivery_address VARCHAR(500),
            order_type VARCHAR(50) DEFAULT 'DELIVERY',
            order_status VARCHAR(50) DEFAULT 'CONFIRMED',
            total_amount DECIMAL(10,2) NOT NULL,
            special_notes VARCHAR(1000),
            created_at TIMESTAMP DEFAULT CURRENT TIMESTAMP
        )
    """),
    ("BB_USERS", """
        CREATE TABLE BB_USERS (
            id INT GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) PRIMARY KEY,
            email VARCHAR(150) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(150) NOT NULL,
            phone VARCHAR(30),
            role VARCHAR(30) NOT NULL DEFAULT 'CUSTOMER',
            created_at TIMESTAMP DEFAULT CURRENT TIMESTAMP
        )
    """),
    ("BB_ADMIN_OPERATORS", """
        CREATE TABLE BB_ADMIN_OPERATORS (
            admin_id INT NOT NULL PRIMARY KEY,
            operator_name VARCHAR(150) NOT NULL,
            phone VARCHAR(30) NOT NULL,
            role VARCHAR(50) NOT NULL,
            assigned_branch VARCHAR(250) NOT NULL,
            can_edit_prices SMALLINT DEFAULT 0,
            can_toggle_inventory SMALLINT DEFAULT 1,
            can_accept_orders SMALLINT DEFAULT 1,
            can_upload_photos SMALLINT DEFAULT 0
        )
    """),
    ("BB_CAKES", """
        CREATE TABLE BB_CAKES (
            sku_id VARCHAR(50) NOT NULL PRIMARY KEY,
            design_code VARCHAR(50),
            name VARCHAR(250) NOT NULL,
            category VARCHAR(50),
            flavor VARCHAR(100),
            sub_category VARCHAR(150),
            available_base_variants VARCHAR(500),
            weight_kg DECIMAL(6,2),
            price DECIMAL(10,2),
            servings VARCHAR(250),
            has_chocochip SMALLINT DEFAULT 0,
            visual_features VARCHAR(1000),
            image_path VARCHAR(500),
            prep_time VARCHAR(100),
            order_confirmation VARCHAR(300),
            description CLOB(10000),
            is_active SMALLINT DEFAULT 1
        )
    """),
    ("BB_CUSTOM_CAKES", """
        CREATE TABLE BB_CUSTOM_CAKES (
            id INT NOT NULL PRIMARY KEY,
            sku_id VARCHAR(50) NOT NULL,
            design_code VARCHAR(50),
            name VARCHAR(250) NOT NULL,
            category VARCHAR(50),
            flavor VARCHAR(100),
            sub_category VARCHAR(150),
            available_base_variants VARCHAR(500),
            service_type VARCHAR(250),
            weight_kg DECIMAL(6,2),
            servings VARCHAR(250),
            has_chocochip SMALLINT DEFAULT 0,
            visual_features VARCHAR(1000),
            image_path VARCHAR(500),
            prep_time VARCHAR(100),
            order_confirmation VARCHAR(300),
            description CLOB(10000),
            price_inr DECIMAL(10,2),
            pricing_type VARCHAR(500),
            ordering_channel VARCHAR(500),
            customization_options VARCHAR(1000),
            price_status VARCHAR(100),
            is_active SMALLINT DEFAULT 1
        )
    """),
    ("BB_PARTY_ACCESSORIES", """
        CREATE TABLE BB_PARTY_ACCESSORIES (
            sku_id VARCHAR(50) NOT NULL PRIMARY KEY,
            item_name VARCHAR(250) NOT NULL,
            category VARCHAR(100),
            sub_category VARCHAR(100),
            pack_size_or_servings VARCHAR(200),
            price_inr DECIMAL(10,2),
            is_vegetarian SMALLINT DEFAULT 1,
            image_path VARCHAR(500),
            visual_features VARCHAR(1000),
            description CLOB(10000),
            is_active SMALLINT DEFAULT 1
        )
    """),
    ("BB_BAKERY_RAW", """
        CREATE TABLE BB_BAKERY_RAW (
            sku_id VARCHAR(50) NOT NULL PRIMARY KEY,
            item_name VARCHAR(250) NOT NULL,
            category_section VARCHAR(100),
            shape VARCHAR(100),
            potato_mash_type VARCHAR(100),
            filling_technique VARCHAR(100),
            has_onion SMALLINT DEFAULT 0,
            has_paneer SMALLINT DEFAULT 0,
            has_egg SMALLINT DEFAULT 0,
            is_eggless SMALLINT DEFAULT 1,
            is_wholesale_eligible SMALLINT DEFAULT 0,
            shelf_life_hours INT DEFAULT 24,
            thermal_type VARCHAR(50),
            description CLOB(10000),
            price_inr DECIMAL(10,2),
            is_active SMALLINT DEFAULT 1
        )
    """)
]


def init_database():
    print("Connecting to IBM Db2 instance IBMDB201...")
    conn = ibm_db.connect(DB2_CONN_STR, "", "")
    print("Connection established successfully!")

    for tbl_name, ddl in TABLES:
        # Check if table exists; drop if needed to allow clean fresh schema
        try:
            ibm_db.exec_immediate(conn, f"DROP TABLE {tbl_name}")
            print(f"Dropped existing table {tbl_name}")
        except Exception:
            pass

        print(f"Creating table {tbl_name}...")
        try:
            ibm_db.exec_immediate(conn, ddl)
            print(f"-> Created {tbl_name} successfully.")
        except Exception as e:
            print(f"Error creating {tbl_name}: {e}")
            ibm_db.close(conn)
            raise e

    ibm_db.close(conn)
    print("All 10 IBM Db2 tables initialized successfully!")


if __name__ == "__main__":
    init_database()
