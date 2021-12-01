# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 1521/11/22 15:43
# @Author  : dongZheX
# @Version : python3.7
# @Desc    : $END$
from SSH import SSHConnection
import argparse
import time
import os
import numpy as np

import json
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d',"--delay", help='time to fresh', type=float, default=1)
    args = parser.parse_args()
    os.system("cls")
    servers = json.load(open("configs/server.json"))
    servers_name = list(servers.keys())
    command = "nvidia-smi --query-gpu=index,temperature.gpu,utilization.gpu,memory.used,memory.total,gpu_name --format=csv,nounits,noheader"
    conns = [SSHConnection(servers[name]['hostname'],port=servers[name]['port'],username=servers[name]['username']
                           ,password=servers[name]['password']) for name in servers_name]# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 1521/11/22 15:43
# @Author  : dongZheX
# @Version : python3.7
# @Desc    : $END$
from SSH import SSHConnection
import argparse
import time
import os
import numpy as np

import json
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d',"--delay", help='time to fresh', type=float, default=1)
    args = parser.parse_args()
    os.system("cls")
    servers = json.load(open("configs/server.json"))
    servers_name = list(servers.keys())
    command = "nvidia-smi --query-gpu=index,temperature.gpu,utilization.gpu,memory.used,memory.total,gpu_name --format=csv,nounits,noheader"
    conns = [SSHConnection(servers[name]['hostname'],port=servers[name]['port'],username=servers[name]['username']
                           ,password=servers[name]['password']) for name in servers_name]
    for conn in conns:
        ret = conn.exec_command("nvidia-smi")
        print(ret.decode())
    for conn in conns:
        conn.close()