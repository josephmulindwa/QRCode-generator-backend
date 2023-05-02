import time
from database import Database

class Request:
    table_name = "requests"
    max_string_length=1000

    def __init__(self):
        self.id=None
        self.name=None
        self.start_value=None
        self.progress=None
        self.total=None
        self.pre_string=None
        self.pro_string=None
        self.csv_serial_length=None
        self.qr_serial_length=None
        self.created_on=None
        self.created_by=None
        self.active=None
        self.complete=None
        self.billed=None
        self.description=None
        self.folder_batch=None
        self.config_error_correct=None
        self.config_box_size=None
        self.config_pad=None
        self.config_fgcolor=None
        self.config_bgcolor=None

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
            active INT,
            complete INT,
            billed INT,
            folder_batch INT,
            config_error_correct VARCHAR(2),
            config_box_size INT,
            config_pad INT,
            config_fgcolor VARCHAR(20),
            config_bgcolor VARCHAR(20)
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
        self.id, self.name, self.description, self.start_value, self.total,\
        self.pre_string, self.pro_string, self.csv_serial_length, self.qr_serial_length,\
        self.created_by, self.created_on, self.progress, self.active, self.complete, self.billed,\
        self.folder_batch, self.config_error_correct, self.config_box_size, self.config_pad,\
        self.config_fgcolor, self.config_bgcolor = data

    def as_dict(self):
        return {self.id, self.name, self.description, self.start_value, self.total,
        self.pre_string, self.pro_string, self.csv_serial_length, self.qr_serial_length,
        self.created_by, self.created_on, self.progress, self.active, self.complete, self.billed,
        self.folder_batch, self.config_error_correct, self.config_box_size, self.config_pad ,
        self.config_fgcolor, self.config_bgcolor}

    @staticmethod
    def insert(name,description,start_value,total,pre_string,pro_string,csv_serial_length,qr_serial_length,created_by,
            folder_batch=100000,progress=0,created_on=None,active=False,complete=False,billed=False,
            config_error_correct="M",config_box_size=4,config_pad=1,config_fgcolor="#000000",config_bgcolor="#ffffff"):
        query = """INSERT INTO {}(
            name,description,start_value,total,pre_string,pro_string,
            csv_serial_length,qr_serial_length,created_by,folder_batch,progress,created_on,
            active,complete,billed,config_error_correct,config_box_size,config_pad,
            config_fgcolor,config_bgcolor)
        VALUES(
            %s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,
            %s,%s
        )""".format(Request.table_name)
        if created_on is None:
            created_on=time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
        Database.execute(query, (name,description,start_value,total,pre_string,pro_string,
            csv_serial_length,qr_serial_length,created_by,folder_batch,progress,created_on,
            int(active),int(complete),int(billed),config_error_correct,config_box_size,config_pad,
            config_fgcolor,config_bgcolor))

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

# __insert_dummy_request()
req = Request.fromName("first_req")

print(req.name)