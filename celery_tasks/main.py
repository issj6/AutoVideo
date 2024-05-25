# 主程序
import os
from celery import Celery
from django.conf import settings
import django

# 把celery和django进行组合，识别和加载django的配置文件
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autovideo.settings')
if not settings.configured:
    django.setup()

# 创建celery实例对象
app = Celery("autovideo")
# 通过app对象加载配置
app.config_from_object("celery_tasks.config")

# 加载任务
# 参数必须必须是一个列表，里面的每一个任务都是任务的路径名称
app.autodiscover_tasks(["celery_tasks.alioss", ])

# 启动Celery的命令
# celery -A celery_tasks.main worker --loglevel=info
