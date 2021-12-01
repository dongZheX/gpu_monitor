# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 1521/11/22 15:43
# @Author  : dongZheX
# @Version : python3.7
# @Desc    : $END$
import paramiko.ssh_exception

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
    while True:
        try:
            time.sleep(args.delay)
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
            os.system('cls')
            for i, rets in enumerate(retss):
                print("====================================%5s====================================" % servers_name[i])
                print("%--25s%-10s%-10s%-10s%-15s%-15s" % (
                "GPU_name", "GPU_id", "Temp", "GPU-Util", "Memory-Usage", "Memory-Free"))
                for gpu in rets:
                    print("%-25s%-10s%-10s%-10s%-15s%-15s" % (
                        gpu[5], gpu[0], gpu[1], gpu[2] + "%", gpu[3] + "/" + gpu[4], int(gpu[4]) - int(gpu[3])))
            print("================================================================================")
        except paramiko.ssh_exception.SSHException:
            conns = [
                SSHConnection(servers[name]['hostname'], port=servers[name]['port'], username=servers[name]['username']
                              , password=servers[name]['password']) for name in servers_name]
    # while True:
    #     os.system("cls")
    # for i, conn in enumerate(conns):
    #     print("============================"+servers_name[i]+"========================")
    #
    #
    # time.sleep(args.delay)
