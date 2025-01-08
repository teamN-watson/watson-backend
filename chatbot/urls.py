from django.urls import path
from chatbot import views

app_name = "chatbot"

urlpatterns = [
    # 챗봇 응답 요청 및 대화 내역 조회
    path("", views.ChatbotAPIView.as_view(), name="chatbot"),
    # 테스트 용 -> 챗봇 마무리 되면 삭제해야 함
    path("test/", views.get_chatbot_answer),
]
