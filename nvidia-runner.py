# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 2021/11/22 21:26
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


var_num = 6
def run_program(server, dir, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli = ssh.connect(server['hostname'], server['port'], server['username'], server['password'], compress=True)
    channel = ssh.invoke_shell()
    sstr = "0"
    while not sstr.endswith('# '):
        stdout = channel.recv(1024)
        sstr = stdout.decode()
    channel.send("cd " + dir+" \n")
    channel.send('nohup ' + command + ' &\n ')
    channel.send('\n')
    sstr = "0"
    id = -2
    while not sstr.endswith('# ') and id != -2:
        stdout = channel.recv(2047)
        time.sleep(0.5)
        sstr = stdout.decode()
        # print(sstr)
        if sstr.find('] ') != -1:
            start = sstr.find('] ')
            end = sstr.find('\r\n',start)
            id = int(sstr[start+2: end])
            break
    channel.close()
    ssh.close()
    return id


def test_finish(tasks, rn):
    for i in range(2, rn + 1):
        if tasks.get_cell_value(i, 7) == "queuing":
            return False
    return True

def is_run(conn, id):

    sstr = conn.exec_command('ps -L '+str(id))
    return True if sstr.decode().find(str(id))!=-1 else False

def get_free_memories(servers_name, conns):
    command = "nvidia-smi --query-gpu=index,temperature.gpu,utilization.gpu,memory.used,memory.total,gpu_name --format=csv,nounits,noheader"
    memories = dict()
    for name in servers_name:
        ret = str(conns[name].exec_command(command))

        start = ret.find('\'')
        end = ret.find('\'', start + 1)
        ret = ret[start + 1:end]
        ret = ret.replace(' ', '')
        ret = ret.replace('\\n', ',')[:-1]
        rets = np.asarray(ret.split(',')).reshape(-1, var_num)
        memories[name] = rets[:, 4].reshape(-1).astype(int) - rets[:, 3].reshape(-1).astype(int)
    return memories

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', "--delay", help='time to fresh', type=float, default=10)
    parser.add_argument('-r', "--repeat", help='repeat to remind', type=float, default=2)
    parser.add_argument('-t', "--task", help='number to remind', type=str, default="task/tasks.xlsx")
    args = parser.parse_args()
    # wb = load_workbook(args.task)
    # ws = wb['排队任务']
    tasks = ExcelOp(args.task)
    rn,cn = tasks.get_row_clo_num()
    # print(rn)
    # print(cn)
    columns = ['id','dir','command','server','gpu','free','state','task_id','入队时间','开始时间','结束时间']
    # 赋值写入时间
    for i in range(2,rn+1):
        if tasks.get_cell_value(i, 1) is not None:
            tasks.set_cell_value(i, 9, time.strftime('%Y-%m-%d %H:%M:%S'))
            tasks.set_cell_value(i, 7, 'queuing')
            tasks.set_cell_value(i, 8, -1)
        else:
            rn = i-1
            break
    # commands
    # 开始资源分配
    ## 读取任务
    commands = []
    for i in range(2, rn+1):
        commands.append({
            "dir":tasks.get_cell_value(i, 2),
            "command":tasks.get_cell_value(i, 3),
            "server":tasks.get_cell_value(i, 4),
            "gpu": tasks.get_cell_value(i, 5),  # 一定要跟命令中对应
            "free": tasks.get_cell_value(i, 6),
            'state': tasks.get_cell_value(i, 7)

        })
    servers = json.load(open("configs/server.json"))
    servers_name = list(servers.keys())

    conns = dict()
    for name in servers_name:
        conns[name] = SSHConnection(servers[name]['hostname'], port=servers[name]['port'], username=servers[name]['username']
                           , password=servers[name]['password'])
    ## 处理任务
    # run_program(servers['Mars'],"shared/dongzhex2/sopool_ppa/","python main_pyg.py > a.out 2>&1")
    flags = np.zeros(len(commands))
    num = rn - 1
    print(str(num)+" Task is queuing......")
    while True:
        try:
            memories = get_free_memories(servers_name, conns)
        except paramiko.ssh_exception.SSHException:

            conns = dict()
            for name in servers_name:
                conns[name] = SSHConnection(servers[name]['hostname'], port=servers[name]['port'],
                                            username=servers[name]['username']
                                            , password=servers[name]['password'])
            memories = get_free_memories(servers_name, conns)
        # print(memories)

        for index, comm in enumerate(commands):
            server = comm['server']
            gpu = comm['gpu']
            command_run = comm['command']
            free = comm['free']
            dir = comm['dir']
            state = comm['state']

            if gpu != -1 and memories[server][gpu] > free and state == 'queuing':
                # 可以运行
                flags[index] += 1
                if flags[index] == args.repeat:
                    try:
                        id = run_program(servers[server], dir, command_run)
                    except Exception as e:
                        id = -2
                    memories[server][gpu] -= free
                    tasks.set_cell_value(index+2, columns.index('task_id')+1, id)
                    tasks.set_cell_value(index+2, columns.index('开始时间')+1, time.strftime('%Y-%m-%d %H:%M:%S'))
                    tasks.set_cell_value(index + 2, columns.index('state')+1, 'running')
                    commands[index]['state'] = "running"
                    print("Task "+str(index+1)+" start with id "+ str(id)+"!")
                    num = num - 1
                    print(str(num) + " Task is queuing........")

            elif gpu == -1 and state == 'queuing':
                # 必须支持指定gpu,暂时没有仔细考虑
                for indexs, mem in enumerate(memories[server]):
                    if mem > free and state == 'queuing':
                        flags[indexs] += 1
                        if flags[indexs] == args.repeat:
                            try:
                                id = run_program(servers[server], dir, command_run)
                            except Exception as e:
                                id = -2
                            tasks.set_cell_value(indexs + 2, columns.index('task_id') + 1, id)
                            tasks.set_cell_value(indexs + 2, columns.index('开始时间') + 1, time.strftime('%Y-%m-%d %H:%M:%S'))
                            tasks.set_cell_value(indexs + 2, columns.index('state') + 1, 'running')
                            commands[indexs]['state'] = "running"
                            print("Task " + str(indexs) + " start with id " + str(id) + "!")
                        break
        # for index, comm in enumerate(commands):
        #     id = tasks.get_cell_value(index+1, columns.index('task_id')+1)
        #     if comm['state'] == "running" and id != -2 and not is_run(conns[comm['server']], id):
        #         comm['state'] = "finish"
        #         tasks.set_cell_value(index + 1, columns.index('state') + 1, 'finish')
        #         tasks.set_cell_value(index + 1, columns.index('结束时间') + 1, time.strftime('%Y-%m-%d %H:%M:%S'))
        if num == 0:
            print("all tasks have get the resources.")
            exit(0)
        time.sleep(args.delay)




if __name__ == "__main__":
    main()


