
from django import forms
from reviews.models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['title', 'content']  # 리뷰 작성에 필요한 필드만 지정
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': '리뷰 제목'}),
            'content': forms.Textarea(attrs={'placeholder': '리뷰 내용을 입력하세요'}),
        }
        labels = {
            'title': '제목',
            'content': '내용',
        }
