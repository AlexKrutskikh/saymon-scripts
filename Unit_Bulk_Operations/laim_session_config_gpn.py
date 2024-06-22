#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

# %%
import datetime as DT
import time
import sys
import glob, os
import json
from calendar import monthrange
import configparser
from nacl import encoding, public

def cswun(cs, en):
    import base64
    import getpass
    from cryptography.fernet import Fernet
    from cryptography.fernet import InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    
    # ---------------
    def encrypted(salt: str, msg: str) -> str:
        """ """
        try:
            f = Fernet(salt)
            encrypted_string = f.encrypt(msg.encode())
        except InvalidToken as err:
            ll.print_log.info("InvalidToken: "+ str(err))    
        return encrypted_string.decode()
    
    # ---------------
    def decrypted(salt: str, msg: str) -> str:
        """ """
        try:
            f = Fernet(salt)
            decrypted_string = f.decrypt(msg.encode())
        except InvalidToken as err:
            ll.print_log.info("InvalidToken: "+ str(err))
        return decrypted_string.decode()
    
    # ---------------
    def gen_salt(password: str) -> str:
        """ """
        salt = b"!+=SaYmOn=+!"  
        back_end = default_backend()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend = back_end
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode()

    key = gen_salt(getpass.getuser())
    if en: 
        cse = encrypted(key,cs.replace('{{','').replace('}}',''))
    else:
        cse = decrypted(key, cs)
    return cse

os.chdir('C:\\Users\kruts\OneDrive\Desktop\PythonProject\saymon-scripts\\Unit_Bulk_Operations')#####
sys.path.append('../Unit_LAIM_Common')
sys.path.append('../Unit_Cloning')

print(os.getcwd())
### configs connect correct ini!!!###
config = configparser.ConfigParser(allow_no_value=True, comment_prefixes='/') # create object to parse data
####### Don't forget to change ######################################
config.read("config_gpn.ini") # read config file
#####################################################################


# os.chdir(config["folders"]["working_path"])
# sys.path.append(config["folders"]["common_laim_path"])
# sys.path.append(config["folders"]["cloning_laim_path"]) df_obj_tree

import laim_logging as ll
ll.logging.config.dictConfig(ll.DEFAULT_LOGGING)

#Read config file

###### Вывод результата на "экран" либо "в лог и в сеть" №#####
just_check = config.getboolean("Cold_start", "just_check")
###############################################################

url = config["saymon_configs"]["url"]
auth = ''
auth_token = ''

if '{{' in config["saymon_configs"]["auth"]:
    #Cyphering secrets
    config["saymon_configs"]["auth"] = cswun(config["saymon_configs"]["auth"], True)
    config["saymon_configs"]["auth_token"] = cswun(config["saymon_configs"]["auth_token"], True)
    with open('config_train.ini', 'w') as configfile:    # save
        config.write(configfile)
    auth = config["saymon_configs"]["auth"].replace('{{','').replace('}}','')
    auth_token = config["saymon_configs"]["auth_token"].replace('{{','').replace('}}','')
else:
    #DeCyphering secrets
    config["saymon_configs"]["auth"] = cswun(config["saymon_configs"]["auth"], False)
    config["saymon_configs"]["auth_token"] = cswun(config["saymon_configs"]["auth_token"], False)
    auth = config["saymon_configs"]["auth"]
    auth_token = config["saymon_configs"]["auth_token"].replace(" ",'')

# custom vars config
cmdb_file = config["saymon_instance_vars"]["cmdb_file"]     
every_day_correction_mode = config["saymon_instance_vars"]["every_day_correction_mode"]
graph_VM_class_id = config["saymon_instance_vars"]["graph_VM_class_id"]
graph_HW_class_id = config["saymon_instance_vars"]["graph_HW_class_id"]

#origin_object_host_oms = config["saymon_instance_vars"]["origin_object_host_oms"] 
#origin_object_host_msk = config["saymon_instance_vars"]["origin_object_host_msk"]

#views
position_dict = json.loads(config["views_params"]["position"])
# oms_shift_left = config["views_params"]["position"]["OMS"]["shift_left"]
# oms_shift_top  = config["views_params"]["position"]["OMS"]["shift_top"]
# msk_shift_left = config["views_params"]["position"]["MSK"]["shift_left"]
# msk_shift_top  = config["views_params"]["position"]["MSK"]["shift_top"]
# step_left      = config["views_params"]["step_left"]
# step_top   =    config["views_params"]["step_top"]
# left =          config["views_params"]["left"]
# top =           config["views_params"]["top"]
# width =         config["views_params"]["width"]
# height =        config["views_params"]["height"]


#parents
dashboard_parents_dict = json.loads(config["parents_configs"]["dashboard_parents_dict"])
# dashboard_parent_list_hw_oms= json.loads(config["parents_configs"]["dashboard_parent_list_hw_oms"])
# dashboard_parent_list_vm_oms= json.loads(config["parents_configs"]["dashboard_parent_list_vm_oms"])
# dashboard_parent_list_hw_msk= json.loads(config["parents_configs"]["dashboard_parent_list_hw_msk"])
# dashboard_parent_list_vm_msk= json.loads(config["parents_configs"]["dashboard_parent_list_vm_msk"])
prop_phys_server = config["parents_configs"]["prop_phys_server"]
prop_virt_server = config["parents_configs"]["prop_virt_server"]
dashboard_host_prefix = json.loads(config["parents_configs"]["dashboard_host_prefix"])

#Правила для клонирования
class_name_stay = config["Cloning_rules"]["class_name_stay"]
origin_object_host = json.loads(config["Cloning_rules"]["origin_object_host"])

####### БИЗНЕС-ЛОГИКА! Динамические шаблоны классов SAYMON (id в меню конфигурации) #######
dict_class_template={
        3: "{\"headlinePropIds\":[\"IP\"],\"custom_style\":\
                {\"zIndex\":9,\"left\":\""+str(25)+
                        "px\",\"top\":\""+str(25)+
                        "px\",\"width\":\""+str(240)+
                        "px\",\"height\":\""+str(135)+
                        "px\"\
                },\
                \"nonPinnedSections\":\
                {\"widgets\":true,\"stat\":true,\"entity-settings\":true,\"monitoring\":true,\
                 \"entity-state-conditions\":true,\"entity-incident-conditions\":true,\"state-triggers\":true,\
                 \"stat-rules\":true,\"properties\":true,\"documents\":true,\"operations\":true,\
                 \"operations-history\":true,\"state-history\":true,\"audit-log\":true,\"history-graph\":true\
                },\
                 \"collapseSections\":\
                {\"ping_rrt\":false,\"packetsTransmitted\":true,\"packetsReceived\":true,\
                 \"packetLossPercentile\":true,\"numberOfErrors\":true,\"numberOfDuplicates\":true,\"roundTripMinimal\":true,\
                 \"roundTripAverage\":true,\"roundTripMaximum\":true,\"exitCode\":true,\"entity-settings\":true,\
                 \"monitoring\":true,\"properties\":false,\"documents\":true\
                }\
             }",
        24: "{\"headlinePropIds\":[\"IP\"],\"custom_style\":\
                {\"zIndex\":9,\"left\":\""+str(25)+
                        "px\",\"top\":\""+str(25)+
                        "px\",\"width\":\""+str(240)+
                        "px\",\"height\":\""+str(135)+
                        "px\"\
                },\
                \"nonPinnedSections\":\
                {\"widgets\":true,\"stat\":true,\"entity-settings\":true,\"monitoring\":true,\
                 \"entity-state-conditions\":true,\"entity-incident-conditions\":true,\"state-triggers\":true,\
                 \"stat-rules\":true,\"properties\":true,\"documents\":true,\"operations\":true,\
                 \"operations-history\":true,\"state-history\":true,\"audit-log\":true,\"history-graph\":true},\
                 \"collapseSections\":{\"ping_rrt\":false,\"packetsTransmitted\":true,\"packetsReceived\":true,\
                 \"packetLossPercentile\":true,\"numberOfErrors\":true,\"numberOfDuplicates\":true,\"roundTripMinimal\":true,\
                 \"roundTripAverage\":true,\"roundTripMaximum\":true,\"exitCode\":true,\"entity-settings\":true,\
                 \"monitoring\":true,\"properties\":false,\"documents\":true},\
                 \"charts\":\
                 [[\"ping_rrt\",[\"{{roundTripMinimal}}\",\"{{roundTripAverage}}\",\"{{roundTripMaximum}}\"]]],\
                 \"widgets\":\
                 [{\"id\":\"ping_rrt_chart\",\"type\":\"chart\",\"parameters\":\
                        {\"metric\":\"[\\\"{{roundTripMinimal}}\\\",\\\"{{roundTripAverage}}\\\",\\\"{{roundTripMaximum}}\\\"]\"}}]}",
        11:"{\"headlinePropIds\":[],\"custom_style\":\
                {\"zIndex\":40,\"left\":\""+str(25)+
                        "px\",\"top\":\""+str(25)+
                        "px\",\"width\":\""+str(240)+
                        "px\",\"height\":\""+str(135)+
                        "px\"\
                },\
                \"backgroundInObj\":true\
            }",
        35:"{\"headlinePropIds\":[],\"showArrow\":true\
            }",
        '63d7a89caeae88225b6d0083': #класс Виртуальная машина - ГПН id 62fe4e0ad40e000023c1d3a2, новые объекты вручную искать в куче на втором экране
            "{\"headlinePropIds\":[],\"custom_style\":{\"zIndex\":\"230"+\
                          ",\"left\":\"2900px\",\"top\":\"30"+\
                          "px\",\"width\":\"28px\",\"height\":\"50px\"},\"nonPinnedSections\":{\"widgets\":\"true\",\
                          \"stat\":\"true\",\"entity-settings\":\"true\",\"monitoring\":\"true\",\
                          \"entity-state-conditions\":\"true\",\"entity-incident-conditions\":\"true\",\
                          \"state-triggers\":\"true\",\"stat-rules\":\"true\",\"properties\":false,\
                          \"documents\":\"true\",\"operations\":\"true\",\"operations-history\":\"true\",\
                          \"state-history\":\"true\",\"audit-log\":\"true\",\"history-graph\":\"true\"},\
                          \"collapseSections\":{\"stat\":\"true\",\"entity-settings\":\"true\",\"monitoring\":\"true\",\
                          \"properties\":false,\"documents\":\"true\"}}"                
        }
###############################################################

#test = False
test_CLI = True
check_ability = True # if needed to check correctness of input id and metrics

if test_CLI: #CLI args emulation for testing
#    sys.argv = ["./bin","week", "1127", 'eth0.incomingBytesPerSecond']
    sys.argv = ["./bin/Unit_Bulk_Operations","Any","Any"]

# parameters from CLI
if (len(sys.argv) == 1) or (sys.argv[1] == "-h"): #help for CLI
    print("Obligatory arguments:\n"\
          "1 arg    :objects ID for processing or 'Any' for whole list\n"\
          "2 arg    :metrics names from Saymon divided by '#', or type 'Any' for whole list\n"\
          "example  :laim_object_metrics_report eth0.incomingBytesor Any PerSecond#eth0.outgoingBytesPerSecond")
    sys.exit()

# Repo for documents uploading and obect_id from CLI (still equal)
if len(sys.argv) > 1:
        object_repo_id = sys.argv[2]
        objects_id_forecast = sys.argv[1]

# metric from CLI 
if len(sys.argv) > 2: #'All' - if load all of objects from saymon   
    try:
        metrics_id_forecast = sys.argv[2].split("#")
    except:
        metrics_id_forecast = sys.argv[2]

# time vars for code and forecasts
time_now = DT.datetime.now()
utc_now = DT.datetime.utcnow()
current_day = time_now.day
current_week_day = time_now.weekday()
current_month = time_now.month
current_year = time_now.year
current_hour = time_now.hour
current_mins = time_now.minute
current_second = time_now.second

# V_START_DATE        = (time_now - DT.timedelta(days= period, minutes=current_mins, seconds=current_second)).strftime('%Y%m%d%H%M%S') #"20220104000000"     # start time imported from cli
# V_END_DATE          = (time_now - DT.timedelta(minutes=current_mins, seconds=current_second)).strftime('%Y%m%d%H%M%S') #"20220204000000"     # end time imported from cli
# #V_END_FORECAST_DATE = (time_now - DT.timedelta(minutes=current_mins, seconds=current_second) + DT.timedelta(days= period)).strftime('%Y%m%d%H%M%S') # "20220304000000"     # end forecast time imported from cli

# V_UTC_START_DATE        = (utc_now - DT.timedelta(days= period, minutes=current_mins, seconds=current_second)).strftime('%Y%m%d%H%M%S') #"20220104000000"     # start time imported from cli
# V_UTC_END_DATE          = (utc_now - DT.timedelta(minutes=current_mins, seconds=current_second)).strftime('%Y%m%d%H%M%S') #"20220204000000"     # end time imported from cli

# V_REP_START_DATE        = (time_now - DT.timedelta(days= period, minutes=current_mins, seconds=current_second)).strftime('%H:%M %d.%m.%Y') # start time imported from cli
# V_REP_END_DATE          = (time_now - DT.timedelta(minutes=current_mins, seconds=current_second)).strftime('%H:%M %d.%m.%Y') # end time imported from cli
#V_REP_END_FORECAST_DATE = (time_now - DT.timedelta(minutes=current_mins, seconds=current_second) + DT.timedelta(days= period)).strftime('%H:%M %d.%m.%Y') # end forecast time imported from cli
V_UTC_TIME_NOW          = time.mktime(time_now.timetuple())# timenow in POSIX format

ll.print_log.info(" - session initiated")
