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
        self.csv_s_length=None
        self.qr_s_length=None
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
            csv_s_length INT,
            qr_s_length INT,
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
        self.__create_table()
    
    @staticmethod
    def fromName(name):
        pass

    @staticmethod
    def fromId(id):
        pass

    def fill_from_data(self, data):
        pass

    @staticmethod
    def insert(name,description,start_value,total,pre_string,pro_string,csv_s_length,qr_s_length,created_by,
            folder_batch=100000,progress=0,created_on=None,active=False,complete=False,billed=False,
            config_error_correct="M",config_box_size=4,config_pad=1,config_fgcolor="(0,0,0)",config_bgcolor="(255,255,255)"):
        query = """INSERT INTO {}(
            name,description,start_value,total,pre_string,pro_string,
            csv_s_length,qr_s_length,created_by,folder_batch,progress,created_on,
            active,complete,billed,config_error_correct,config_box_size,config_pad,
            config_fgcolor,config_bgcolor)
        VALUES(
            %s,%s,%d,%d,%s,%s,
            %d,%d,%d,%d,%s,%s,
            %d,%d,%d,%s,%d%d,
            %s,%s
        )"""
        if created_on is None:
            created_on=time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
        Database.execute(query, (name,description,start_value,total,pre_string,pro_string,
            csv_s_length,qr_s_length,created_by,folder_batch,progress,created_on,
            active,complete,billed,config_error_correct,config_box_size,config_pad,
            config_fgcolor,config_bgcolor))

