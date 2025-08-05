import pymysql

def get_db():
    """
    MySQL 데이터베이스 연결 객체 반환
    환경에 맞게 host/user/password/database 값을 수정하세요.
    """
    return pymysql.connect(
        host="localhost",  
        user="root",       
        password="1234",  
        database="modular_agents_db",  
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )
