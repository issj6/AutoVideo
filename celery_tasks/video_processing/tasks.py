from time import sleep

from celery_tasks.functions.audio_translation.audio_translation import audio_translation
from celery_tasks.functions.extraction_subtitle.extraction_subtitle import extraction_subtitle
from celery_tasks.functions.video_translation.video_translation import video_translation
from celery_tasks.main import app
from tasks.models import Task


@app.task
def add_task(task_object):
    task_type = task_object.get('task_type')
    print(f"任务类型：{task_type}")
    try:
        if task_type == 1:
            video_translation(task_object)
        elif task_type == 2:
            audio_translation(task_object)
        elif task_type == 3:
            extraction_subtitle(task_object)
    except Exception as e:
        task = Task.objects.get(pk=task_object.get("id"))
        task.task_status = 5
        task.task_msg = str(e)
        task.save()
