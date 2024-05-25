from rest_framework import serializers

from files import models


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class FileSerializer(serializers.ModelSerializer):
    upload_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    last_use_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    user = serializers.PrimaryKeyRelatedField(
        queryset=models.File.objects.all(),
        write_only=True
    )
    file_source = serializers.CharField(source="get_file_source_display")
    file_path = serializers.CharField(write_only=True)

    class Meta:
        model = models.File
        fields = "__all__"
