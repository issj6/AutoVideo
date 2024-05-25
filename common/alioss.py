import os

import oss2

# 配置阿里云OSS
access_key_id = 'xxxxxx'
access_key_secret = 'xxxxxx'
endpoint = 'xxxxxx'
bucket_name = 'xxxxxx'


def upload(file, filename):
    # 初始化OSS存储
    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)

    return bucket.put_object(filename, file)


def sign_url(filename):
    # 初始化OSS存储
    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)

    return bucket.sign_url('GET', filename, 60)


def download(filename, save_folder):
    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    result = bucket.get_object(filename)
    save_path = os.path.join(save_folder, filename)
    with open(save_path, 'wb') as file:
        file.write(result.read())

    return save_path
