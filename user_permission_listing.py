from database import Database

class UserPermissionListing:
    table_name="user_permission_listing"

    def __init__(self):
        Database.init()
        UserPermissionListing.init()

    @staticmethod
    def __create_table():
        query = """CREATE TABLE {} (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT,
            permission_id INT,
            granted_by INT
        )""".format(UserPermissionListing.table_name)
        Database.execute(query)

    def init():
        if not Database.check_table_exists(UserPermissionListing.table_name):
            UserPermissionListing.__create_table()
    
    @staticmethod
    def insert_listing(user_id, permission_id, granted_by=None):
        """inserts permission listing"""
        query = """INSERT INTO {}(user_id,permission_id,granted_by) VALUES(%s,%s,%s)""".format(
            UserPermissionListing.table_name)
        Database.execute(query, (user_id, permission_id, granted_by))