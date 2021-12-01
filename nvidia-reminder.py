# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 2021/11/22 17:56
# @Author  : dongZheX
# @Version : python3.7
# @Desc    : $END$
from SSH import SSHConnection
import argparse
import time
import os
import numpy as np
import util
import json
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f',"--free", help='free to remind', type=float, default=5000)
    parser.add_argument('-d', "--delay", help='delay to monitor', type=float, default=5)
    parser.add_argument('-r', "--repeat", help='repeat to remind', type=float, default=2)
    parser.add_argument('-n', "--number", help='number to remind', type=int, default=2)

    args = parser.parse_args()
    servers = json.load(open("configs/server.json"))
    servers_name = list(servers.keys())
    command = "nvidia-smi --query-gpu=index,temperature.gpu,utilization.gpu,memory.used,memory.total,gpu_name --format=csv,nounits,noheader"
    conns = [SSHConnection(servers[name]['hostname'],port=servers[name]['port'],username=servers[name]['username']
                           ,password=servers[name]['password']) for name in servers_name]
    number = 0
    flag = np.zeros((len(conns), 16))
    while True:

        retss = []
        for i, conn in enumerate(conns):
            ret = str(conns[i].exec_command(command))
            start = ret.find('\'')
            end = ret.find('\'', start + 1)
            ret = ret[start + 1:end]
            ret = ret.replace(' ', '')
            ret = ret.replace('\\n', ',')[:-1]
            # print(ret)
            retss.append(np.asarray(ret.split(',')).reshape(-1, 6))
            # print(rets)
        for index, rets in enumerate(retss):
            for i,gpu in enumerate(rets):
                if int(gpu[4]) - int(gpu[3]) > args.free:
                    flag[index][i] += 1
                if int(gpu[4]) - int(gpu[3]) < args.free:
                    flag[index][i] = 0
                    number -= 1

        message = ""
        for i,vs in enumerate(flag):
            for j,v in enumerate(vs):
                if v == args.repeat:
                    message += servers_name[i]+"-"+"GPU"+retss[i][j][0]+"-"+retss[i][j][5]+" has " + str(int(retss[i][j][4]) - int(retss[i][j][3])) + " free memory." + "\n"
                    number += 1
        if message != "":
            util.tell_me('0',message)
           # time.sleep(1000)
        if number >= args.number:
            exit(0)
        time.sleep(args.delay)


