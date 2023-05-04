from database import Database
import json

class Configuration:
    table_name="configurations"
    default_config_name="default_config"
    error_correction_levels = ["ERROR_CORRECT_M", "ERROR_CORRECT_L", "ERROR_CORRECT_H", "ERROR_CORRECT_Q"]
    versions = [1]

    def __init__(self):
        self.id=None
        self.name=None
        self.user_id=None
        self.folder_batch=None
        self.version=None
        self.error_correction=None
        self.box_size=None
        self.border=None
        self.fgcolor=None
        self.bgcolor=None

        Database.init()
        self.__setup()

    def __create_table(self):
        query = """CREATE TABLE {} (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(225),
            user_id INT,
            folder_batch INT,
            version INT,
            error_correction VARCHAR(40),
            box_size INT,
            border INT,
            fgcolor VARCHAR(10),
            bgcolor VARCHAR(10)
        )""".format(Configuration.table_name)
        Database.execute(query)
    
    def __setup(self):
        if not Database.check_table_exists(Configuration.table_name):
            self.__create_table()

    @staticmethod
    def fromName(name):
        configuration = Configuration()
        configs = Database.fetch_rows_by_condition(Configuration.table_name, {"name":[name, "s"]})
        if configs is not None and len(configs)>0:
            configuration = Configuration()
            configuration.fill_from_data(configs[0])
        else:
            configuration = None
        return configuration

    @staticmethod
    def fromId(id):
        configuration = Configuration()
        configs = Database.fetch_rows_by_condition(Configuration.table_name, {"id":[id, "s"]})
        if configs is not None and len(configs)>0:
            configuration = Configuration()
            configuration.fill_from_data(configs[0])
        else:
            configuration = None
        return configuration
    
    @staticmethod
    def fromData(data):
        config = Configuration()
        config.fill_from_data(data)
        return config
    
    def fill_from_data(self, data):
        (self.id,self.name,self.user_id,self.folder_batch,self.version,
        self.error_correction,self.box_size,self.border,self.fgcolor,self.bgcolor) = data

    def as_dict(self):
        return {"id":self.id, "name":self.name, "user_id":self.user_id,"folder_batch":self.folder_batch,"version":self.version,
        "error_correction":self.error_correction,"box_size":self.box_size,"border":self.border,
        "fgcolor":self.fgcolor,"bgcolor":self.bgcolor}

    @staticmethod
    def insert(name,user_id,folder_batch,version,error_correction,box_size,border,fgcolor,bgcolor):
        """inserts configuration"""
        query = """INSERT INTO {}(name,user_id,folder_batch,version,error_correction,box_size,border,fgcolor,bgcolor)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""".format(Configuration.table_name)
        Database.execute(query, (name,user_id,folder_batch,version,error_correction,box_size,border,fgcolor,bgcolor))

    @staticmethod
    def insert_default_config(user_id):
        config = Configuration.get_default_config()
        Configuration.insert(name=Configuration.default_config_name, user_id=user_id, **config)

    @staticmethod
    def get_default_config():
        with open("config.json") as fr:
            config = json.load(fr)
            return config

    @staticmethod
    def get_configurations_by_id(id):
        rows = Database.fetch_rows_by_condition(Configuration.table_name, {"user_id":[id, "s"]})
        if rows is not None and len(rows)>0:
            configs = [Configuration.fromData(data) for data in rows]
            return configs
        return None

    @staticmethod
    def get_configurations_by_name(name):
        rows = Database.fetch_rows_by_condition(Configuration.table_name, {"name":[name, "s"]})
        if rows is not None and len(rows)>0:
            configs = [Configuration.fromData(data) for data in rows]
            return configs
        return None

    @staticmethod
    def get_configuration_by_id_and_name(id, name):
        rows = Database.fetch_rows_by_condition(Configuration.table_name, {"user_id":[id, "s"],"name":[name, "s"]})
        if rows is not None and len(rows)>0:
            config = Configuration.fromData(rows[0])
            return config
        return None
    
    @staticmethod
    def get_error_correction_levels():
        return ["ERROR_CORRECT_M", "ERROR_CORRECT_L", "ERROR_CORRECT_H", "ERROR_CORRECT_Q"]

    @staticmethod
    def find_configurations_like(pattern, user_id=None):
        configs = Database.fetch_rows_like(Configuration.table_name, "name", pattern, user_id=user_id)
        if configs is not None:
            return [Configuration.fromData(data)  for data in configs]
        return None