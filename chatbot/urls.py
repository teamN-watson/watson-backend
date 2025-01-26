from django.urls import path
from chatbot import views

app_name = "chatbot"

urlpatterns = [
    # 챗봇 응답 요청 및 초기화
    path("", views.ChatbotAPIView.as_view(), name="chatbot"),
    # 대화 내역 로드
    path("record/", views.ChatbotRecordAPIView.as_view(), name="chatbot_record"),
    # 대화 메시지 삭제
    path("<int:messageid>/", views.DeleteChatbotRecordAPIView.as_view(), name="delete_record"),
    # 자동 사용자 맞춤 게임 추천
    path("auto/", views.AutoChatbotAPIView.as_view(), name="auto_chatbot"),
]
