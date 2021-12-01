# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 2021/11/29 20:12
# @Author  : dongZheX
# @Version : python3.7
# @Desc    : $END$
import threading
from openpyxl import load_workbook
import argparse
import time
from ExcelOp import ExcelOp
from SSH import SSHConnection
import json
import numpy as np
import paramiko
import queue
from task import Task


def priority_key(e):
    return e.priority


class gpu_runner(threading.Thread):
    def __init__(self, name, threadID, server, gpu_id, timeout=20):
        threading.Thread.__init__(self)
        self.name = name
        self.server = server
        self.threadID = threadID
        self.var_num = 6
        self.fflush = 0
        self.conn = None
        self.init()
        self.gpu_id = gpu_id
        self.memory = self.get_memory()
        self.finish = False
        self.tasks = list()
        self.tail = 0
        self.state = threading.Condition()  # 暂时未使用
        self.append_lock = threading.Event()
        self.append_lock.set()
        self.wait_append_lock = threading.Event()
        self.new_task = False
        self.__flag = threading.Event()
        self.__flag.set()
        self.__running = threading.Event()
        self.__running.set()

    def init(self):
        self.conn = SSHConnection(self.server['hostname'], self.server['port'], self.server['username'],
                                  self.server['password'])

    def pause(self):
        self.__flag.clear()

    def resume(self):
        self.__flag.set()

    def run_program(self, dir, command):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.server['hostname'], self.server['port'], self.server['username'], self.server['password'],
                    compress=True)
        channel = ssh.invoke_shell()
        sstr = "0"
        while not sstr.endswith('# '):
            stdout = channel.recv(1024)
            sstr = stdout.decode()
        channel.send("cd " + dir + " \n")
        channel.send('nohup ' + command + ' &\n ')
        channel.send('\n')
        sstr = "0"
        id = -2
        while not sstr.endswith('# ') and id == -2:
            stdout = channel.recv(2047)
            time.sleep(0.5)
            sstr = stdout.decode()
            # print(sstr)
            if sstr.find('] ') != -1:
                start = sstr.find('] ')
                end = sstr.find('\r\n', start)
                id = int(sstr[start + 2: end])
                break
        channel.close()
        ssh.close()
        return id

    def append_task(self, task):
        self.append_lock.wait()
        self.wait_append_lock.clear()
        if len(self.tasks) == 0:
            self.tasks.append(task)
            self.wait_append_lock.set()
            return True

        pointer = self.tail + 1 if self.tail != 0 else 0
        while pointer < len(self.tasks):
            if self.tasks[pointer].priority < task.priority:
                pointer += 1
                continue
            elif self.tasks[pointer].priority == task.priority and self.tasks[pointer].free <= task.free:
                pointer += 1
                continue
            else:
                break
        self.tasks.insert(pointer, task)
        self.new_task = True
        self.wait_append_lock.set()

    def delete_task(self, id):
        self.append_lock.wait()
        self.wait_append_lock.clear()
        pointer = self.tail + 1 if self.tail != 0 else 0
        while pointer < len(self.tasks):
            if self.tasks[pointer].id == id:
                self.tasks.pop(pointer)
                self.wait_append_lock.set()
                return True

            pointer += 1

        self.wait_append_lock.set()
        return True

    def change_task(self, id, task):
        self.append_lock.wait()
        self.wait_append_lock.clear()

        pointer = self.tail + 1 if self.tail != 0 else 0
        while pointer < len(self.tasks):
            if self.tasks[pointer].id == id:
                self.tasks.pop(pointer)
                self.append_task(task)
                self.wait_append_lock.set()
                return True
            pointer += 1
        self.wait_append_lock.set()
        return False

    def run(self) -> None:
        while self.__running.isSet():
            self.__flag.wait()
            self.append_lock.clear()
            if len(self.tasks) == 0 or not self.wait_append_lock.isSet():
                self.append_lock.set()
                self.wait_append_lock.wait()

            while self.tail != len(self.tasks) and self.tasks[self.tail].state != "queuing":
                self.append_lock.set()
                self.__flag.wait()
                self.append_lock.clear()
                self.tail += 1
            if self.tail == len(self.tasks):

                self.append_lock.set()
                self.wait_append_lock.clear()
                self.wait_append_lock.wait()
                self.append_lock.clear()

            task = self.tasks[self.tail]
            self.new_task = False
            dir, command, free, state = task.dir, task.command, task.free, task.state
            self.append_lock.set()
            while True and not self.new_task:
                self.__flag.wait()
                try:
                    self.memory = self.get_memory()
                except paramiko.ssh_exception.SSHException:
                    self.init()
                    self.memory = self.get_memory()
                if free < self.memory:
                    self.tail = self.tail + 1
                    try:
                        id = self.run_program(dir, command)
                        print()
                        print("===============================================================")
                        print("task-" + str(task.id) + " is running with id " + str(id) + " in " + self.name)
                        print("===============================================================")
                        print()
                    except Exception:
                        id = -2
                    finally:
                        task.state = "Processing"
                        if command.find(".sh") != -1:
                            self.fflush += free
                        else:
                            while True:
                                self.__flag.wait()
                                find__ = False
                                find_ = False
                                time.sleep(3)
                                try:
                                    find__ = self.find_nvidia_pid(id)
                                    find_ = self.find_ps_pid(id)
                                except paramiko.ssh_exception.SSHException:

                                    self.init()
                                    find__ = self.find_nvidia_pid(id)
                                    find_ = self.find_ps_pid(id)
                                finally:
                                    if find__ is True:
                                        task.state = "Running"
                                        task.running_time = time.strftime('%Y-%m-%d %H:%M:%S')
                                        task.ps_id = id
                                        break
                                    if find_ is False:
                                        task.state = "Error"
                                        break
                        break
                if not self.__running.isSet():
                    break

            if not self.__running.isSet():
                self.conn.close()
                break

    def find_ps_pid(self, id):
        command = "ps aux | awk '{print $2}'| grep -w " + str(id)
        try:
            ret = self.conn.exec_command(command)
        except paramiko.ssh_exception.SSHException:
            self.init()
            ret = self.conn.exec_command(command)
        return ret is not None

    def find_nvidia_pid(self, id):
        command = "nvidia-smi --query-compute-apps=pid  --format=csv,nounits,noheader"
        try:
            ret = self.conn.exec_command(command)
        except paramiko.ssh_exception.SSHException:
            self.init()
            ret = self.conn.exec_command(command)
        ret = np.asarray(ret.decode().split('\n')[:-1], dtype=int)
        if np.where(ret == id)[0].shape[0] != 0:
            return True
        else:
            return False

    def stop(self):
        self.__running.clear()
        # self.conn.close()

    def get_memory(self):
        command = "nvidia-smi --query-gpu=index,temperature.gpu,utilization.gpu,memory.used,memory.total,gpu_name --format=csv,nounits,noheader"
        memories = dict()
        ret = str(self.conn.exec_command(command))
        start = ret.find('\'')
        end = ret.find('\'', start + 1)
        ret = ret[start + 1:end]
        ret = ret.replace(' ', '')
        ret = ret.replace('\\n', ',')[:-1]
        rets = np.asarray(ret.split(',')).reshape(-1, self.var_num)
        memory = rets[:, 4].reshape(-1).astype(int) - rets[:, 3].reshape(-1).astype(int) - self.fflush
        return memory[self.gpu_id]

    # def print_queuing(self):
    #     qsize = self.tasks.qsize()
    #     if qsize == 0:
    #         print(self.name + " has finished all tasks")
    #     else:
    #         for i in range(qsize):
    #             task = self.tasks.get()
    #             self.tasks.put(task)
    #             print("%--25s%-10s%-10s%-10s%-15s%-15s" % (
    #                 "GPU", "task_priority", "task_dir", "task_command"))
    #             for gpu in rets:
    #                 print("%-25s%-10s%-10s%-10s%-15s%-15s" % (
    #                     gpu[5], gpu[0], gpu[1], gpu[2] + "%", gpu[3] + "/" + gpu[4], int(gpu[4]) - int(gpu[3])))
    #
    # def print_finish(self):
    #     print("ok")

# thread1 = gpu_runner("Polaris-gpu1",1, {'hostname':'211.81.55.150','port':20051,'username':'root','password':'Dz471371..'},0)
# print(thread1.memory)
# thread1.append_task(Task("dongZheX/fog_ogb", "python main_arxiv.py --device 0", 10000, 100))
# print(thread1.tasks)
# task = thread1.tasks[0]
# task.state = "running"
#
# thread1.start()
# thread1.append_task(Task("dongZheX/fog_ogb", "python main_arxiv.py --device 0", 10000, 1))
# print(thread1.tasks)
# print(thread1.tasks[1].state)
#
#
#
# thread1.join()
# #
