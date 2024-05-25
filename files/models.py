from django.db import models

from users.models import User


# Create your models here.


class File(models.Model):
    filename = models.CharField(max_length=128)
    save_name = models.CharField(max_length=128, default=None)
    file_path = models.CharField(max_length=128, null=True, blank=True)
    file_url = models.CharField(max_length=128, null=True, blank=True)
    file_type = models.CharField(max_length=32)
    upload_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_source = models.IntegerField(choices=((1, "用户上传"), (2, "任务生成")), default=1)
    last_use_time = models.DateTimeField(null=True, blank=True)
