from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Conversation(models.Model):
    '''
    유저의 대화방 번호 저장
    '''
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_adult = models.BooleanField(default=False)

    def __str__(self):
        return f"Conversation #{self.id} - {self.user}"


class Message(models.Model):
    '''
    대화내역 저장
    '''
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    content = models.JSONField()
    is_user = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{'User' if self.is_user else 'Bot'}] {self.content[:30]}"

