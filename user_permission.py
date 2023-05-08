from database import Database

class UserPermission:
    table_name = "user_permissions"
    last_permission = "DELETE_USERS" # to-do

    permission_list = [
        ["GRANT_U_PERMISSIONS", "GRANT USER PERMISSIONS", "Grant user permissions"],
        ["VIEW_U_PERMISSIONS", "VIEW USER PERMISSIONS", "View user permissions"],
        ["VIEW_M_PERMISSIONS", "VIEW PERSONAL PERMISSIONS", "View personal permissions"],
        ["APPROVE_USERS", "APPROVE USERS", "Approve user accounts"],
        ["CREATE_USERS","CREATE USERS", "Create user accounts"],
        ["CREATE_REQUESTS", "CREATE REQUESTS","Make Requests"],
        ["VIEW_USERS", "VIEW USERS", "View Users"],
        ["VIEW_M_REQUESTS", "VIEW PERSONAL REQUESTS", "View personal requests"],
        ["VIEW_U_REQUESTS", "VIEW USER REQUESTS", "View user requests"],
        ["EDIT_M_PROFILE", "EDIT PERSONAL PROFILE", "Edit personal profile"],
        ["EDIT_U_PROFILES", "EDIT USER PROFILES", "Edit user profiles"],
        ["BILL_REQUESTS", "BILL REQUESTS", "Bill user requests"],
        ["DELETE_REQUESTS", "DELETE REQUESTS", "Delete user requests"],
        ["DELETE_USERS", "DELETE USERS","Delete User Accounts"]
    ]

    def __init__(self):
        Database.init()
        UserPermission.init()

    @staticmethod
    def __create_table():
        query = """CREATE TABLE {} (
            id INT PRIMARY KEY AUTO_INCREMENT,
            code VARCHAR(225) UNIQUE,
            name VARCHAR(225),
            description VARCHAR(255)
        )""".format(UserPermission.table_name)
        Database.execute(query)
    
    @staticmethod
    def __insert_permissions():
        """setup after creating tables"""
        # atomic : insert roles
        for (code, name, desc) in UserPermission.permission_list:
            UserPermission.insert_permission(code, name, description=desc)
    
    @staticmethod
    def init():
        if not Database.check_table_exists(UserPermission.table_name):
            UserPermission.__create_table()
            UserPermission.__insert_permissions()
    
    @staticmethod
    def insert_permission(code, name, description):
        """inserts permissions"""
        query = """INSERT INTO {}(code,name,description) VALUES(%s,%s,%s)""".format(
            UserPermission.table_name)
        Database.execute(query, (code, name, description))

    @staticmethod
    def get_permissions():
        return UserPermission.permission_list
    
    @staticmethod
    def get_permissions_as_dict():
        return [{"code":code,"name":name,"description":description} for code,name,description in UserPermission.permission_list]

    @staticmethod
    def get_permission_codes():
        return [code for (code,_,__) in UserPermission.permission_list]

    @staticmethod
    def get_id_from_code(code):
        for i in range(len(UserPermission.permission_list)):
            _code, _, __ = UserPermission.permission_list[i]
            if _code==code:
                return i+1
        return None

    @staticmethod
    def get_ids_from_codes(codes):
        ids = [UserPermission.get_id_from_code(code) for code in codes]
        return ids
    
    @staticmethod
    def get_code_from_id(c_id):
        for i in range(len(UserPermission.permission_list)):
            _code, _, __ = UserPermission.permission_list[i]
            if (i+1)==c_id:
                return _code
        return None
    
    @staticmethod
    def get_codes_from_ids(ids):
        codes = [UserPermission.get_code_from_id(c_id for c_id in ids)]
        return codes
    
    @staticmethod
    def get_default_user_permission_ids():
        codes = ["CREATE_REQUESTS", "VIEW_M_REQUESTS", "EDIT_M_PROFILE"]
        return UserPermission.get_ids_from_codes(codes)
