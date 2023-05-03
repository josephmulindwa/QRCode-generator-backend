from database import Database
from user_permission import UserPermission
from user_permission_listing import UserPermissionListing
from request import Request
from configuration import Configuration

class User:
    table_name = "users" 
    superadmin = {
        "name":"SUPER ADMIN",
        "username":"superadmin",
        "email":"super@admin.com",
        "password":"superadmin@i23",
        "created_by":None,
        "approved":True
    }
    root_username="superadmin"
    def __init__(self):
        self.id=None
        self.name=None
        self.username=None
        self.email=None
        self.password=None
        self.created_by=None
        self.approved=None
        Database.init()
        Request()
        Configuration()
        self.__setup()

    def __create_table(self):
        query = """CREATE table {} (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(225),
            username VARCHAR(225) UNIQUE,
            email VARCHAR(225),
            password VARCHAR(255),
            created_by INT,
            approved INT
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

    @staticmethod
    def fromData(data):
        user = User()
        user.fill_from_data(data)
        return user

    def as_dict(self):
        return {"id":self.id,"name":self.name,"username":self.username,"email":self.email,
        "password":self.password,"created_by":self.created_by,"approved":self.approved}

    def fill_from_data(self, data):
        self.id,self.name,self.username,self.email,self.password,self.created_by,self.approved = data
    
    def __setup(self):
        """setup after creating tables"""
        if not Database.check_table_exists(User.table_name):
            self.__create_table()
            # atomic : add user
            superadmin_id = self.add_user(User.superadmin['name'],User.superadmin['username'],User.superadmin['email'],
                User.superadmin['password'],User.superadmin['created_by'],User.superadmin['approved'])
            # add base permissions
            UserPermission() #.init
            permission_data = UserPermission.get_permission_codes()
            permission_ids = UserPermission.get_ids_from_codes(permission_data)
            userpermissionlisting = UserPermissionListing()
            for permission_id in permission_ids:
                UserPermissionListing.insert_listing(superadmin_id, permission_id)
            
    @staticmethod
    def fetch_rows_by_condition(condition):
        user_data = Database.fetch_rows_by_condition(User.table_name, condition_dict=condition)
        users = None
        if user_data is not None and len(user_data)>0:
            users = [User.fromData(data) for data in user_data]
        return users

    def insert_user(self, name, username, email, password, created_by=None, approved=False):
        """adds user"""
        if created_by is None:
            created_by = self.id
        query = "INSERT INTO {}(name,username,email,password,created_by,approved) VALUES(%s,%s,%s,%s,%s,%s)".format(User.table_name)
        Database.execute(query, (name,username,email,password,created_by,approved))
    
    def add_user(self, name, username, email, password, created_by=None, approved=False):
        """adds user and sets up dependencies -> returns id"""
        # insert
        self.insert_user(name,username,email,password,created_by,approved)
        users = Database.fetch_rows_by_condition(User.table_name, {"username":[username, "s"]})
        user_data = users[0]
        _id = user_data[0]
        # add config
        Configuration.insert_default_config(_id)
        return _id

    def grant_permissions(self, permission_list):
        # UserPermissionListing.get
        pass

    def get_request(self, name):
        """
        gets the request with this name that belongs to the user
        """
        import request
        rows = Database.fetch_rows_by_condition(table_name=Request.table_name, condition_dict={"name":[name, 's'], "created_by":[self.id, 's']})
        if rows is not None and len(rows)>0:
            return rows[0]
        return None

    def add_new_request(self,name,description,start_value,total,pre_string,pro_string,csv_serial_length,qr_serial_length,
            configuration_id,progress=0,created_on=None,state=Request.STATE_ACTIVE):
        Request.insert(name,description,start_value,total,pre_string,pro_string,csv_serial_length,qr_serial_length,self.id,
            progress,created_on,state,configuration_id)

    def get_configuration_by_name(self, name):
        return Configuration.get_configuration_by_id_and_name(self.id, name)

    def get_requests(self, category=None):
        condition = {"created_by":[self.id, 's']}
        if category is not None:
            if category=='ALL':
                pass
            elif category=="INACTIVE":
                condition["state"] = ["CANCELLED", "s"]
            else:
                condition["state"] = [category, "s"]
        requests = Request.fetch_rows_by_condition(condition)
        return requests
        
    def get_user(self, username):
        users = User.fetch_rows_by_condition(condition={"username":[username, "s"]})
        if users is not None and len(users)>0:
            return users[0]
        return None

    def get_users(self):
        users = User.fetch_rows_by_condition(dict())
        if users is None:
            return []
        return users
    
    def add_configuration(self, name, folder_batch, version, error_correction, box_size, border, fgcolor, bgcolor):
        Configuration.insert(name, self.id, folder_batch, version, error_correction, box_size, border, fgcolor, bgcolor)
    
    def get_configurations(self):
        return Configuration.get_configurations_by_id(self.id)

        

#user = User()
#user.add_new_request("n", "", 0, 200,"", "", 3, 5, configuration_id=1)