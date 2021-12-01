# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 2021/11/29 17:46
# @Author  : dongZheX
# @Version : python3.7
# @Desc    : $END$
from openpyxl import load_workbook
import argparse
import time
from ExcelOp import ExcelOp
from SSH import SSHConnection
import json
import numpy as np
import paramiko
servers = json.load(open("configs/server.json"))
servers_name = list(servers.keys())
command = "nvidia-smi --query-compute-apps=pid --format=csv,nounits,noheader"
conns = dict()
for name in servers_name:
    conns[name] = SSHConnection(servers[name]['hostname'], port=servers[name]['port'],
                                username=servers[name]['username']
                                , password=servers[name]['password'])
servers = ['Polaris','Fanyan','Mars']
# servers = ['stark']
# ret = conns[servers[0]].exec_command(command)
# ret = np.asarray(ret.decode().split('\n')[:-1],dtype=int)
# print(ret)
with open("feature_code.txt", "r") as f:
    lines = f.readlines()
    feature_code = [s.replace('\n','') for s in lines]
times = 0
print("Killing the Bad Guy!!!")
while True:

    times += 1
    if times % 30 == 0:
        with open("feature_code.txt", "r") as f:
            lines = f.readlines()
            feature_code = [s.replace('\n', '') for s in lines]
    time.sleep(3)
    try:
        for name in servers:
            for code in feature_code:
                conns[name].exec_command("ps aux|grep " + str(code) + ("|awk '{print $2}'|xargs kill -9"))
                # ret = conns[name].exec_command(command)
                # if ret is not None:
                #     start = ret.find('\'')
                #     end = ret.find('\'', start + 1)
                #     ret = ret[start + 1:end]
                #     ret = ret.replace(' ', '')
                #     ret = ret.replace('\\n', ',')[:-1]
                #     ret = np.asarray(ret.split(',')).reshape(-1, 6)
                #     print(ret)
    except paramiko.ssh_exception.SSHException:
        conns = dict()
        for name in servers_name:
            conns[name] = SSHConnection(servers[name]['hostname'], port=servers[name]['port'],
                                        username=servers[name]['username']
                                        , password=servers[name]['password'])