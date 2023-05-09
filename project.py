import utils
from database import Database

class Project:
    STATE_ACTIVE="ACTIVE"
    STATE_BILLED="BILLED"
    STATE_PAUSED="PAUSED"
    STATE_CANCELLED="CANCELLED"
    STATE_COMPLETE="COMPLETE"

    table_name = "projects"
    max_string_length=1000

    def __init__(self):
        self.id=None
        self.name=None
        self.description=None
        self.start_value=None
        self.progress=None
        self.total=None
        self.pre_string=None
        self.pro_string=None
        self.csv_serial_length=None
        self.qr_serial_length=None
        self.created_on=None
        self.created_by=None
        self.state=None
        self.configuration_id=None

        Database.init()
        Project.init()

    @staticmethod
    def __create_table():
        query = """CREATE TABLE {} (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(225),
            description VARCHAR(225),
            start_value INT,
            total INT,
            pre_string VARCHAR({}),
            pro_string VARCHAR({}),
            csv_serial_length INT,
            qr_serial_length INT,
            created_by INT,
            created_on VARCHAR(40),
            progress INT,
            state VARCHAR(10),
            configuration_id INT
        )""".format(Project.table_name, Project.max_string_length, Project.max_string_length)
        Database.execute(query)
    
    @staticmethod
    def init():
        if not Database.check_table_exists(Project.table_name):
            Project.__create_table()
    
    @staticmethod
    def fromName(name):
        Project.init()
        projects = Database.fetch_rows_by_condition(Project.table_name, {"name":[name]})
        if projects is not None:
            project = Project()
            project.fill_from_data(projects[0])
        else:
            project = None
        return project

    @staticmethod
    def fromId(id):
        Project.init()
        projects = Database.fetch_rows_by_condition(Project.table_name, {"id":[id]})
        if projects is not None:
            project = Project()
            project.fill_from_data(projects[0])
        else:
            project = None
        return project

    def fill_from_data(self, data):
        (self.id, self.name, self.description, self.start_value, self.total,\
        self.pre_string, self.pro_string, self.csv_serial_length, self.qr_serial_length,\
        self.created_by, self.created_on, self.progress, self.state, self.configuration_id) = data

    @staticmethod
    def fromData(data):
        req = Project()
        req.fill_from_data(data)
        return req

    def as_dict(self):
        return {"id":self.id, "name":self.name, "description":self.description, "start":self.start_value, "total":self.total,
        "pre_string":self.pre_string, "pro_string":self.pro_string, "csv_serial_length":self.csv_serial_length, 
        "qr_serial_length":self.qr_serial_length, "created_by":self.created_by, "created_on":self.created_on, 
        "progress":self.progress, "state":self.state, "config_id":self.configuration_id}

    @staticmethod
    def insert(name,description,start_value,total,pre_string,pro_string,csv_serial_length,qr_serial_length,created_by,
            progress=0,created_on=None,state=STATE_ACTIVE, configuration_id=None):
        query = """INSERT INTO {}(
            name,description,start_value,total,pre_string,pro_string,csv_serial_length,
            qr_serial_length,created_by,progress,created_on,state,configuration_id)
        VALUES(
            %s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s
        )""".format(Project.table_name)
        if created_on is None:
            created_on=utils.get_time_string()
        Database.execute(query, (name,description,start_value,total,pre_string,pro_string,csv_serial_length,
        qr_serial_length,created_by,progress,created_on,state,configuration_id))
    
    @staticmethod
    def fetch_rows_by_condition(condition_dict):
        projects = Database.fetch_rows_by_condition(Project.table_name, condition_dict)
        if projects is not None and len(projects)>0:
            return [Project.fromData(data) for data in projects]
        return None
    
    @staticmethod
    def count_projects(user_id=None, category="ALL"):
        condition=dict()
        if category in [Project.STATE_ACTIVE, Project.STATE_BILLED, Project.STATE_CANCELLED, Project.STATE_COMPLETE, Project.STATE_PAUSED]:
            condition["state"] = [category]
        elif category!="ALL":
            return None
        if user_id is not None:
            condition["created_by"]=[user_id]
        count_data = Database.count_rows_by_condition(Project.table_name, condition)
        if count_data is not None and type(count_data)==list:
            return count_data[0][0]
        return None

    @staticmethod
    def find_projects_like(pattern, user_id=None):
        projects = Database.fetch_rows_like(Project.table_name, "name", pattern, created_by=user_id)
        if projects is not None:
            return [Project.fromData(data) for data in projects]
        return None


def __insert_dummy_project():
    Project()
    Project.insert(
        name="first_req",
        description="test project",
        start_value=0,
        total=1000,
        pre_string='SN',
        pro_string='',
        csv_serial_length=3,
        qr_serial_length=5,
        created_by=1
    )

#__insert_dummy_project()
#req = Project.fromName("first_req")
#print(req.name)