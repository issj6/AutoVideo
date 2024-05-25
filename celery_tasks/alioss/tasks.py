import os

import oss2

import files
from celery_tasks.main import app
from files.models import File
import os

from tasks.models import Task

# 配置阿里云OSS
access_key_id = 'xxxxxx'
access_key_secret = 'xxxxxx'
endpoint = 'xxxxxx'
bucket_name = 'xxxxxx'


# @app.task
# def upload_alioss_from_object(filename, file_object):
#     try:
#         auth = oss2.Auth(access_key_id, access_key_secret)
#         bucket = oss2.Bucket(auth, endpoint, bucket_name)
#         bucket.put_object(filename, file_object)
#
#     except Exception as e:
#         print(e)
#         return str(e)


@app.task
def upload_alioss_from_file(filename, file_path, task_id=None, delete_old=False):
    try:
        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        bucket.put_object_from_file(filename, file_path)

        # 上传完成后，删除本地文件
        os.remove(file_path)

        # 更新数据库
        if task_id:
            task = Task.objects.get(pk=task_id)
            task.source_file = filename
            task.save()

        if delete_old:
            # 删除数据库中保存的该文件的本地路径
            file = File.objects.filter(save_name=filename).first()
            if file:
                file.file_path = None
                file.save()

    except Exception as e:
        return str(e)


@app.task
def delete_alioss_file(filename):
    try:
        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        bucket.delete_object(filename)

    except Exception as e:
        return str(e)
