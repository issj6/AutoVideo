import requests


def download_file(url, file_path):
    # 发送 HTTP GET 请求获取文件
    response = requests.get(url)

    # 检查请求是否成功
    if response.status_code == 200:
        # 打开文件用于写入
        with open(file_path, 'wb') as file:
            # 以块的方式写入文件
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return True
    else:
        # 如果请求失败，打印错误信息
        print(f"Error: Unable to download file. HTTP status code: {response.status_code}")
        raise Exception(f"Error: Unable to download file. HTTP status code: {response.status_code}")
