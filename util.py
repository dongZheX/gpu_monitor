# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 2021/11/22 17:43
# @Author  : dongZheX
# @Version : python3.7
# @Desc    : $END$
import requests
import json
def tell_me(status,  str):

    data = {
        "msg_type": "post",
        "content": {
        "post": {
            "zh_cn": {
                "title": "GPU空闲提醒",
                "content": [
                    [
                        {
                            "tag": "text",
                            "text": str
                        },
                    ]
                ]
            }
        }
    }
    }
    requests.post(url="https://open.feishu.cn/open-apis/bot/v2/hook/08743930-2b14-4727-9476-16b551d3a9f0", headers={'Content-Type': 'application/json'}, data=json.dumps(data))
