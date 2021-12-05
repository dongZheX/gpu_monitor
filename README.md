# gpu_monitor
A demo that remotely seize the server resources.

## Requirement
```sh
pip install paramiko 
pip uninstall cryptography 
pip install cryptography   
```

## How to use

1. Configure the configs/server.json
2. python nvidia-runner++.py

## Feature

1. Use module `Task Manager` to import tasks to GPUs.  
   1.1. You can add new task by keyboard or Excel (template in task directory).  
1.2 You can delete or change the task in "queuing" state (Bad settings because of not useing queue structure).  
   1.3 You can save the present task.
2. Use module `GPU Monitor` to monitor the gpu remotely.
3. User module `GPU Runner` to start, pause, resume and stop the thread which seize the server resources.
