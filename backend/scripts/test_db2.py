import ibm_db

conn_str = 'DATABASE=IBMDB201;HOSTNAME=127.0.0.1;PORT=50000;PROTOCOL=TCPIP;UID=dbayush;PWD=8844;'
conn = ibm_db.connect(conn_str, '', '')

sql_drop = 'DROP TABLE BAKEBOX_TEST'
try:
    ibm_db.exec_immediate(conn, sql_drop)
except Exception:
    pass

sql_create = '''
CREATE TABLE BAKEBOX_TEST (
    id INT NOT NULL PRIMARY KEY,
    name VARCHAR(100),
    data CLOB(10000)
)
'''
ibm_db.exec_immediate(conn, sql_create)

sql_insert = "INSERT INTO BAKEBOX_TEST (id, name, data) VALUES (1, 'Shri Ram Baker', '{\"tag\": \"fresh cakes\"}')"
ibm_db.exec_immediate(conn, sql_insert)

sql_select = 'SELECT id, name, data FROM BAKEBOX_TEST WHERE id = 1'
stmt = ibm_db.exec_immediate(conn, sql_select)
row = ibm_db.fetch_assoc(stmt)
print("Fetched Row successfully:", row)

ibm_db.exec_immediate(conn, sql_drop)
ibm_db.close(conn)
print("IBM Db2 connection and table lifecycle verified 100%!")
