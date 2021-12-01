# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 2021/11/30 13:13
# @Author  : dongZheX
# @Version : python3.7
# @Desc    : $END$
import time


class Task:
    def __init__(self, dir, command, free, priority, id):
        self.dir = dir
        self.command = command
        self.free = free
        self.start_time = time.strftime('%Y-%m-%d %H:%M:%S')
        self.running_time = 0
        self.state = "queuing"
        self.priority = priority
        self.id = id
        self.ps_id = 0

    def __eq__(self, other):
        return self.priority == other.priority

    def __le__(self, other):
        return self.priority > other.priority

    def __gt__(self, other):
        return self.priority < other.priority

