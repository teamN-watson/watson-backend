import os
from django.core.files.storage import FileSystemStorage
from django.conf import settings


class OverwriteStorage(FileSystemStorage):
    """
    file 같은 이름 존재시 overwrite
    """

    def get_available_name(self, name, max_length=20):
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name


def rename_imagefile_to_uid(instance, filename):
    upload_to = "images/profile/"
    ext = filename.split(".")[-1]

    if instance.user_id:
        uid = instance.user_id
        filename = "{}.{}".format(uid, ext)

    return os.path.join(upload_to, filename)
