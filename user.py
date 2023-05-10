from database import Database
from user_permission import UserPermission
from user_permission_listing import UserPermissionListing
from project import Project
from configuration import Configuration

class User:
    default_approve_state=False
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
        Project.init()
        Configuration.init()
        UserPermission.init()
        UserPermissionListing.init()
        self.__setup()

    @staticmethod
    def __create_table():
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

    def __setup(self):
        """setup after creating tables"""
        if not Database.check_table_exists(User.table_name):
            User.__create_table()
            # add super user
            permission_data = UserPermission.get_permission_codes()
            permission_ids = UserPermission.get_ids_from_codes(permission_data)
            self.add_user(User.superadmin['name'],User.superadmin['username'],User.superadmin['email'],
                User.superadmin['password'],User.superadmin['created_by'],User.superadmin['approved'], permission_ids)

    @staticmethod
    def fromUsername(username):
        user = User()
        users = Database.fetch_rows_by_condition(User.table_name, {"username":[username]})
        if users is not None and len(users)>0:
            user = User()
            user.fill_from_data(users[0])
        else:
            user = None
        return user

    @staticmethod
    def fromEmail(email):
        user = User()
        users = Database.fetch_rows_by_condition(User.table_name, {"email":[email]})
        if users is not None and len(users)>0:
            user = User()
            user.fill_from_data(users[0])
        else:
            user = None
        return user

    @staticmethod
    def fromId(id):
        user = User()
        users = Database.fetch_rows_by_condition(User.table_name, {"id":[id]})
        if users is not None and len(users)>0:
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
            
    @staticmethod
    def fetch_rows_by_condition(condition):
        user_data = Database.fetch_rows_by_condition(User.table_name, condition_dict=condition)
        users = None
        if user_data is not None and len(user_data)>0:
            users = [User.fromData(data) for data in user_data]
        return users

    @staticmethod
    def insert_user(name, username, email, password, created_by=None, approved=default_approve_state):
        """atomic insert user"""
        query = "INSERT INTO {}(name,username,email,password,created_by,approved) VALUES(%s,%s,%s,%s,%s,%s)".format(User.table_name)
        Database.execute(query, (name,username,email,password,created_by,approved))
    
    def add_user(self, name, username, email, password, created_by=None, approved=False, permission_ids=None):
        """adds user and sets up dependencies -> returns id"""
        # insert
        if created_by is None:
            created_by = self.id
        User.insert_user(name,username,email,password,created_by,approved)
        users = Database.fetch_rows_by_condition(User.table_name, {"username":[username]})
        user_data = users[0]
        _id = user_data[0]
        # add config
        Configuration.insert_default_config(_id)
        if permission_ids is None:
            permission_ids=UserPermission.get_default_user_permission_ids()
        for permission_id in permission_ids:
            UserPermissionListing.insert_listing(_id, permission_id, granted_by=self.id)
        return _id

    def grant_permissions(self, user_id, permission_ids):
        if user_id==self.id:
            return False
        UserPermissionListing.delete_user_permissions(user_id)
        for perm_id in permission_ids:
            granted = UserPermissionListing.insert_listing(user_id, perm_id, self.id, check_exists=False)
        return True

    def get_project(self, name):
        """
        gets the project with this name that belongs to the user
        """
        rows = Project.fetch_rows_by_condition(condition_dict={"name":[name], "created_by":[self.id]})
        if rows is not None and len(rows)>0:
            return rows[0]
        return None

    def add_new_project(self,name,description,start_value,total,pre_string,pro_string,csv_serial_length,qr_serial_length,
            configuration_id,progress=0,created_on=None,state=Project.STATE_ACTIVE):
        Project.insert(name,description,start_value,total,pre_string,pro_string,csv_serial_length,qr_serial_length,self.id,
            progress,created_on,state,configuration_id)

    def get_configuration_by_name(self, name):
        return Configuration.get_configuration_by_id_and_name(self.id, name)

    def get_projects(self, category=None):
        condition = {"created_by":[self.id]}
        if category is not None:
            if category=='ALL':
                pass
            elif category=="INACTIVE":
                condition["state"] = ["CANCELLED"]
            else:
                condition["state"] = [category]
        projects = Project.fetch_rows_by_condition(condition)
        return projects
        
    def get_user(self, username):
        users = User.fetch_rows_by_condition(condition={"username":[username]})
        if users is not None and len(users)>0:
            return users[0]
        return None

    def get_users(self):
        # returns list of all users except self
        users = User.fetch_rows_by_condition({"username":[self.username, None, "!="]})
        if users is None:
            return []
        return users
    
    def find_users_like_name(self, name):
        rows = Database.fetch_rows_like(User.table_name, "name", name)
        if rows is not None:
            users = [User.fromData(data) for data in rows]
            return users
        return None
    
    def find_users_like_username(self, username):
        rows = Database.fetch_rows_like(User.table_name, "username", username)
        if rows is not None:
            users = [User.fromData(data) for data in rows]
            return users
        return None

    def find_projects_like(self, pattern):
        return Project.find_projects_like(pattern, self.id) #depending on permission

    def find_configurations_like(self, pattern):
        return Configuration.find_configurations_like(pattern, self.id)
    
    def add_configuration(self, name, folder_batch, version, error_correction, box_size, border, fgcolor, bgcolor):
        Configuration.insert(name, self.id, folder_batch, version, error_correction, box_size, border, fgcolor, bgcolor)
    
    def get_configurations(self):
        return Configuration.get_configurations_by_id(self.id)

    def count_users(self):
        count_data = Database.count_rows_by_condition(User.table_name, {})
        if count_data is not None and type(count_data)==list:
            return max(0, count_data[0][0]-1)
        return None

    def count_all_projects(self, category="ALL"):
        return Project.count_projects(user_id=None, category=category)

    def count_projects(self, category="ALL"):
        # counts projects for this user_id that have state=category
        return Project.count_projects(user_id=self.id, category=category)
    
    def get_permissions(self):
        listings = UserPermissionListing.get_listings_for_id(self.id)
        return listings
    
    def get_permissions_for_user(self, user_id):
        return UserPermissionListing.get_listings_for_id(user_id)

        