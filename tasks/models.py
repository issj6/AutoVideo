from django.db import models

from files.models import File
from users.models import User


# Create your models here.

class Function(models.Model):
    title = models.CharField(max_length=32)
    description = models.TextField(null=True, blank=True)
    image = models.CharField(max_length=128, null=True, blank=True,
                             default="https://marketplace.canva.com/dmwQE/MAFo9ddmwQE/1/tl/canva-MAFo9ddmwQE.png")
    router = models.CharField(max_length=32, default=None, unique=True)


class Task(models.Model):
    task_name = models.CharField(max_length=128, verbose_name="任务名称")
    # source_file = models.OneToOneField(File, models.CASCADE, verbose_name="任务源文件", related_name="source_file")
    # res_file = models.OneToOneField(File, models.CASCADE, null=True, blank=True, verbose_name="任务结果文件",
    #                                 related_name="res_file")
    original_filename = models.CharField(max_length=128, null=True, blank=True, verbose_name="原文件名", default=None)
    source_file = models.CharField(max_length=128, null=True, blank=True, verbose_name="任务源文件")
    res_file = models.CharField(max_length=128, null=True, blank=True, verbose_name="任务结果文件")
    user = models.ForeignKey(User, models.CASCADE, verbose_name="任务创建用户", default=None)
    task_status = models.IntegerField(choices=(
        (1, "等待中"),
        (2, "正在处理"),
        # (3, "等待核对"),
        (3, "处理完成"),
        (4, "处理失败")
    ), default=1, verbose_name="任务状态")
    task_args = models.CharField(max_length=2048, null=True, blank=True, verbose_name="任务参数")
    # task_type = models.CharField(max_length=128, null=True, blank=True, verbose_name="任务类型")
    task_type = models.ForeignKey(Function, models.CASCADE, default=None)
    task_processing_id = models.CharField(max_length=128, null=True, blank=True, verbose_name="任务处理ID")
    task_msg = models.TextField(null=True, blank=True, verbose_name="任务当前信息")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    start_processing_time = models.DateTimeField(null=True, blank=True, verbose_name="开始处理时间")
    end_processing_time = models.DateTimeField(null=True, blank=True, verbose_name="结束处理时间")
