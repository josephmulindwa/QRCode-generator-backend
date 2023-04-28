from database import Database
from user_permission import UserPermission#
from user_permission_listing import UserPermissionListing

class User:
    table_name = "users" 
    superadmin = {
        "name":"SUPER ADMIN",
        "username":"superadmin",
        "email":"super@admin.com",
        "password":"superadmin@i23",
        "created_by":None
    }
    root_username="superadmin"
    def __init__(self):
        self.id=None
        self.name=None
        self.username=None
        self.email=None
        self.password=None
        self.created_by=None

        Database.init()
        self.__setup()


    def __create_table(self):
        query = """CREATE table {} (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(225),
            username VARCHAR(225) UNIQUE,
            email VARCHAR(225),
            password VARCHAR(255),
            created_by INT
        )""".format(User.table_name)
        Database.execute(query)
    
    @staticmethod
    def fromUsername(username):
        user = User()
        users = Database.fetch_rows_by_condition(User.table_name, {"username":[username, "s"]})
        if users is not None:
            user = User()
            user.fill_from_data(users[0])
        else:
            user = None
        return user

    @staticmethod
    def fromEmail(email):
        user = User()
        users = Database.fetch_rows_by_condition(User.table_name, {"email":[email, "s"]})
        if users is not None:
            user = User()
            user.fill_from_data(users[0])
        else:
            user = None
        return user

    @staticmethod
    def fromId(id):
        user = User()
        users = Database.fetch_rows_by_condition(User.table_name, {"id":[id, "i"]})
        if users is not None:
            user = User()
            user.fill_from_data(users[0])
        else:
            user = None
        return user

    def as_dict(self):
        return {"id":self.id,"name":self.name,"username":self.username,"email":self.email,
        "password":self.password,"created_by":self.created_by}

    def fill_from_data(self, data):
        self.id, self.name, self.username, self.email, self.password, self.created_by = data
    
    def __setup(self):
        """setup after creating tables"""
        if not Database.check_table_exists(User.table_name):
            self.__create_table()
            # atomic : add user
            self.insert_user(User.superadmin['name'],User.superadmin['username'],User.superadmin['email'],
                User.superadmin['password'],User.superadmin['created_by'])
            users = Database.fetch_rows_by_condition(User.table_name, {"name":[User.superadmin['name'], "s"]})
            user_data = users[0]
            superadmin_id = user_data[0]
            # add base permissions
            UserPermission() #.init
            permission_data = UserPermission.get_permission_codes()
            permission_ids = UserPermission.get_ids_from_codes(permission_data)
            userpermissionlisting = UserPermissionListing()
            for permission_id in permission_ids:
                UserPermissionListing.insert_listing(superadmin_id, permission_id)

    def insert_user(self, name, username, email, password, created_by=None):
        """adds user"""
        if created_by is None:
            created_by = self.created_by
        query = "INSERT INTO {}(name,username,email,password,created_by) VALUES(%s,%s,%s,%s,%s)".format(User.table_name)
        Database.execute(query, (name, username, email, password, created_by))
