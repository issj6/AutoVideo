import json
import os
import time

import requests

from celery_tasks.functions.common.utils import subtitle_handler


def log_time(func):
    def wrapper(*args, **kw):
        begin_time = time.time()
        func(*args, **kw)
        print('识别字幕总用时：{time}'.format(time=time.time() - begin_time))

    return wrapper


def speech_to_subtitle(file_path, language='zh-CN', caption_type='speech', words_per_line=30):
    base_url = 'xxxxxx'
    appid = "xxxxxx"
    access_token = "xxxxxx"

    file_len = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    file_type_text = file_name.split('.')[-1]
    response = requests.post(
        '{base_url}/submit'.format(base_url=base_url),
        params=dict(
            appid=appid,
            language=language,
            # use_itn='True',
            use_capitalize='True',
            max_lines=1,
            words_per_line=words_per_line,
            caption_type=caption_type,
            # use_ddc='True'
        ),
        headers={
            'content-type': f'audio/{file_type_text}',
            'Connection': 'keep-alive',
            'Content-Length': str(file_len),
            'Authorization': 'Bearer; {}'.format(access_token)
        },
        data=open(file_path, 'rb').read(file_len)
    )
    print('submit response = {}'.format(response.text))
    assert (response.status_code == 200)
    assert (response.json()['message'] == 'Success')

    job_id = response.json()['id']
    response = requests.get(
        '{base_url}/query'.format(base_url=base_url),
        params=dict(
            appid=appid,
            id=job_id,
        ),
        headers={
            'Authorization': 'Bearer; {}'.format(access_token)
        }
    )
    assert (response.status_code == 200)
    content = response.json()
    # print(content)
    # 处理返回结果
    subtitles = subtitle_handler(content)
    return subtitles
