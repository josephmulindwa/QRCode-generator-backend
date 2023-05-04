import mysql.connector 

class Database:
    connection=None
    DB_NAME="qrcode"

    @staticmethod
    def init():
        try:
            if Database.connection is None:
                Database.connection = mysql.connector.connect(host="localhost",user="root")
                Database.__create_database()
        except Exception as e:
            print("Database failed to initialize :", e)
            exit(1)

    @staticmethod
    def __create_database():
        query = "CREATE DATABASE IF NOT EXISTS {}".format(Database.DB_NAME)
        Database.execute(query)
        Database.execute(query="USE {}".format(Database.DB_NAME))

    @staticmethod
    def execute(query, fields=(), fecthable=False):
        try:
            cursor = Database.connection.cursor(buffered=True)
            cursor.execute(query, fields)
            result = None
            if fecthable:
                result = cursor.fetchall()
            Database.connection.commit()
            cursor.close()
            return result
        except mysql.connector.Error as err:
            print("Execution failed : {}".format(err))
            exit(1)
        return False

    @staticmethod
    def check_table_exists(table_name):
        query = "SHOW TABLES LIKE '{}'".format(table_name)
        tables = Database.execute(query, fecthable=True)
        return (tables is not None)

    @staticmethod
    def construct_where_clause(condition_dict):
        # col:[val, type, boolean_binder]
        clause = ""
        values = []
        cols = list(condition_dict.keys())
        for i in range(len(cols)):
            col = cols[i]
            data = condition_dict[col]
            _value = data[0]
            _type = data[1]
            _bool = data[2] if len(data)>2 else 'and'
            s = "{}=%{} ".format(col, _type)
            if i<len(cols)-1:
                s += _bool+" "
            clause += s
            values.append(_value)
        return clause, values

    @staticmethod
    def get_hash(string):
        return string

    @staticmethod
    def fetch_rows_by_condition(table_name, condition_dict):
        clause, values = Database.construct_where_clause(condition_dict)
        where_clause = "WHERE "+clause if len(values) > 0 else ""
        query = "SELECT * FROM {} {}".format(table_name, where_clause)
        return Database.execute(query, values, fecthable=True)
    
    @staticmethod
    def count_rows_by_condition(table_name, condition_dict, count_field="id"):
        clause, values = Database.construct_where_clause(condition_dict)
        where_clause = "WHERE "+clause if len(values) > 0 else ""
        query = "SELECT COUNT({}) FROM {} {}".format(count_field,table_name, where_clause)
        return Database.execute(query, values, fecthable=True)

    @staticmethod
    def fetch_rows_like(table_name, column, pattern, user_id=None, created_by=None):
        where_id_clause = ""
        if user_id is not None:
            where_id_clause = " user_id={} AND ".format(user_id)
        elif created_by is not None:
            where_id_clause = " created_by={} AND ".format(created_by)
        query = """SELECT * FROM {} WHERE {} {} LIKE '%{}%'""".format(table_name, where_id_clause, column, pattern)
        return Database.execute(query, [], fecthable=True)