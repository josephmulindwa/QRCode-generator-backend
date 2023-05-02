from database import Database

class UserPermission:
    table_name = "user_permissions"

    permission_list = [
        ["GRANT_U_PERMISSIONS", "GRANT USER PERMISSIONS"],
        ["VIEW_U_PERMISSIONS", "VIEW USER PERMISSIONS"],
        ["VIEW_M_PERMISSIONS", "VIEW PERSONAL PERMISSIONS"],
        ["APPROVE_USERS", "APPROVE USERS"],
        ["CREATE_USERS","CREATE USERS"],
        ["CREATE_REQUESTS", "CREATE REQUESTS"],
        ["VIEW_USERS", "VIEW USERS"],
        ["VIEW_M_REQUESTS", "VIEW PERSONAL REQUESTS"],
        ["VIEW_U_REQUESTS", "VIEW USER REQUESTS"],
        ["VIEW_U_COMPLETE_REQUESTS", "VIEW USER COMPLETE REQUESTS"],
        ["VIEW_U_BILLED_REQUESTS", "VIEW USER BILLED REQUESTS"],
        ["VIEW_U_CANCELLED_REQUESTS", "VIEW USER CANCELLED REQUESTS"],
        ["VIEW_U_ACTIVE_REQUESTS", "VIEW USER ACTIVE REQUESTS"],
        ["EDIT_M_PROFILE", "EDIT PERSONAL PROFILE"],
        ["EDIT_U_PROFILES", "EDIT USER PROFILES"],
        ["BILL_REQUESTS", "BILL REQUESTS"],
        ["DELETE_REQUESTS", "DELETE REQUESTS"],
        ["DELETE_USERS", "DELETE USERS"]
    ]

    def __init__(self):
        Database.init()
        self.__setup()

    def __create_table(self):
        query = """CREATE TABLE {} (
            id INT PRIMARY KEY AUTO_INCREMENT,
            code VARCHAR(225) UNIQUE,
            name VARCHAR(225),
            description VARCHAR(255)
        )""".format(UserPermission.table_name)
        Database.execute(query)
    
    def __insert_permissions(self):
        """setup after creating tables"""
        # atomic : insert roles
        for arr in UserPermission.permission_list:
            code, name = arr
            self.insert_permission(code, name, description="place_holder_none")
    
    def __setup(self):
        if not Database.check_table_exists(UserPermission.table_name):
            self.__create_table()
            self.__insert_permissions()
    
    def insert_permission(self, code, name, description):
        """inserts permissions"""
        query = """INSERT INTO {}(code,name,description) VALUES(%s,%s,%s)""".format(
            UserPermission.table_name)
        Database.execute(query, (code, name, description))

    @staticmethod
    def get_permissions():
        return UserPermission.permission_list

    @staticmethod
    def get_permission_codes():
        return [code for (code,_) in UserPermission.permission_list]

    @staticmethod
    def get_id_from_code(code):
        for i in range(len(UserPermission.permission_list)):
            _code, _ = UserPermission.permission_list[i]
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
            _code, _ = UserPermission.permission_list[i]
            if (i+1)==c_id:
                return _code
        return None
    
    @staticmethod
    def get_codes_from_ids(ids):
        codes = [UserPermission.get_code_from_id(c_id for c_id in ids)]
        return codes
