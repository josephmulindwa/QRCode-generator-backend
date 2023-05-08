from database import Database

class UserPermissionListing:
    table_name="user_permission_listing"

    def __init__(self):
        self.id=None
        self.user_id=None
        self.permission_id=None
        self.granted_by=None

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
    def fromData(data):
        listing = UserPermissionListing()
        listing.fill_from_data(data)
        return listing
        
    def fill_from_data(self, data):
        self.id, self.user_id, self.permission_id, self.granted_by = data

    def as_dict(self):
        return {"id":self.id, "user_id":self.user_id, "permission_id":self.permission_id, "granted_by":self.granted_by}
    
    @staticmethod
    def insert_listing(user_id, permission_id, granted_by=None, check_exists=False):
        """inserts permission listing"""
        if check_exists:
            rows = Database.fetch_rows_by_condition(UserPermissionListing.table_name, {"user_id":[user_id], "permission_id":[permission_id]})
            if rows is not None and len(rows)>0:
                return
        query = """INSERT INTO {}(user_id,permission_id,granted_by) VALUES(%s,%s,%s)""".format(
            UserPermissionListing.table_name)
        Database.execute(query, (user_id, permission_id, granted_by))

    @staticmethod
    def get_listings_for_id(user_id):
        rows = Database.fetch_rows_by_condition(UserPermissionListing.table_name, {"user_id":[user_id]})
        if rows is not None:
            return [UserPermissionListing.fromData(data) for data in rows]
        return None
    
    @staticmethod
    def delete_user_permissions(user_id):
        return Database.delete_rows_by_condition(UserPermissionListing.table_name, {"user_id":[user_id]})