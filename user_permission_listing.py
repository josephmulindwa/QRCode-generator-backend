from database import Database

class UserPermissionListing:
    table_name="user_permission_listing"

    def __init__(self):
        Database.init()
        self.__setup()

    def __create_table(self):
        query = """CREATE TABLE {} (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT,
            permission_id INT,
            granted_by INT
        )""".format(UserPermissionListing.table_name)
        Database.execute(query)
    
    def __setup(self):
        if not Database.check_table_exists(UserPermissionListing.table_name):
            self.__create_table()
    
    @staticmethod
    def insert_listing(user_id, permission_id, granted_by=None):
        """inserts permission listing"""
        query = """INSERT INTO {}(user_id,permission_id,granted_by) VALUES(%s,%s,%s)""".format(
            UserPermissionListing.table_name)
        Database.execute(query, (user_id, permission_id, 0))