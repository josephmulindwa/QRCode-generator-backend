import mysql.connector 
# ---this file is abit obsolete

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
            else:
                result=True
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
        return (tables is not None and len(tables)>0)

    @staticmethod
    def construct_where_clause(condition_dict):
        """
        condition_dict : dictionary
            Signature : {col : [val, [boolean_binder, op_binder]}
            Example : {'id':[3], 'name':['j', 'or'], 'age':[99, None, '!=']}
            Resolves to : "id=3 or name='j' and age!=99"

            Default boolean binder : `and`
            Default op_binder : `=`
        """
        clause = ""
        values = []
        cols = list(condition_dict.keys())
        for i in range(len(cols)):
            col = cols[i]
            args = condition_dict[col]
            _value, _bbinder, _opbinder = args[0], 'and', '='
            if len(args)>1 and args[1] is not None:
                _bbinder=args[1]
            if len(args)>2 and args[2] is not None:
                _opbinder=args[2]
            if i==0:
                _bbinder=""
            s = "{} {}{}%s ".format(_bbinder, col, _opbinder)
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
    
    @staticmethod
    def delete_rows_by_condition(table_name, condition_dict):
        clause, values = Database.construct_where_clause(condition_dict)
        where_clause = "WHERE "+clause if len(values) > 0 else ""
        query = "DELETE FROM {} {}".format(table_name, where_clause)
        return Database.execute(query, values, fecthable=False)