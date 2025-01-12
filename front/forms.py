# forms.py
from django import forms
from reviews.models import Review
from django.conf import settings

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['title', 'content', 'app_id', 'score', 'categories']  # 모델의 필드와 일치시킴

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 예를 들어, form에서 score를 기본값으로 0으로 설정할 수 있음
        if not self.instance.pk:  # 새로 작성하는 경우
            self.fields['score'].initial = 0

    def clean_app_id(self):
        app_id = self.cleaned_data.get('app_id')
        if app_id is None:
            raise forms.ValidationError("게임 ID(app_id)는 필수입니다.")
        return app_id

    def clean_score(self):
        score = self.cleaned_data.get('score')
        if score is not None and (score < 0 or score > 5):
            raise forms.ValidationError("평점은 0.0에서 5.0 사이여야 합니다.")
        return score
