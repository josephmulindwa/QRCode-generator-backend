import time
from database import Database

class Request:
    STATE_ACTIVE="ACTIVE"
    STATE_BILLED="BILLED"
    STATE_PAUSED="PAUSED"
    STATE_CANCELLED="CANCELLED"
    STATE_COMPLETE="COMPLETE"

    table_name = "requests"
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
        self.__setup()

    def __create_table(self):
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
        )""".format(Request.table_name, Request.max_string_length, Request.max_string_length)
        Database.execute(query)

    def __setup(self):
        if not Database.check_table_exists(Request.table_name):
            self.__create_table()
    
    @staticmethod
    def fromName(name):
        request = Request()
        requests = Database.fetch_rows_by_condition(Request.table_name, {"name":[name, "s"]})
        if requests is not None:
            request = Request()
            request.fill_from_data(requests[0])
        else:
            request = None
        return request

    @staticmethod
    def fromId(id):
        request = Request()
        requests = Database.fetch_rows_by_condition(Request.table_name, {"id":[id, "s"]})
        if requests is not None:
            request = Request()
            request.fill_from_data(requests[0])
        else:
            request = None
        return request

    def fill_from_data(self, data):
        (self.id, self.name, self.description, self.start_value, self.total,\
        self.pre_string, self.pro_string, self.csv_serial_length, self.qr_serial_length,\
        self.created_by, self.created_on, self.progress, self.state, self.configuration_id) = data

    @staticmethod
    def fromData(data):
        req = Request()
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
        )""".format(Request.table_name)
        if created_on is None:
            created_on=time.strftime("%d/%m/%Y %H:%M", time.localtime())
        Database.execute(query, (name,description,start_value,total,pre_string,pro_string,csv_serial_length,
        qr_serial_length,created_by,progress,created_on,state,configuration_id))
    
    @staticmethod
    def fetch_rows_by_condition(condition_dict):
        requests = Database.fetch_rows_by_condition(Request.table_name, condition_dict)
        if requests is not None and len(requests)>0:
            return [Request.fromData(data) for data in requests]
        return None

def __insert_dummy_request():
    Request()
    Request.insert(
        name="first_req",
        description="test request",
        start_value=0,
        total=1000,
        pre_string='SN',
        pro_string='',
        csv_serial_length=3,
        qr_serial_length=5,
        created_by=1
    )

#__insert_dummy_request()
#req = Request.fromName("first_req")
#print(req.name)