from rest_framework import serializers
from .models import Review, ReviewComment, ReviewLike, ReviewCommentLike

class ReviewCommentSerializer(serializers.ModelSerializer):
    """ReviewComment 모델 직렬화"""
    nickname = serializers.SerializerMethodField()

    class Meta:
        model = ReviewComment
        fields = ['id', 'review', 'user', 'nickname', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'review', 'created_at', 'updated_at']

    def get_nickname(self, obj):
        """유저 닉네임 반환 (유저가 없으면 '알수없음')"""
        return obj.user.nickname if obj.user else "알수없음"


class ReviewCommentLikeSerializer(serializers.ModelSerializer):
    """ReviewCommentLike 모델 직렬화"""

    class Meta:
        model = ReviewCommentLike
        fields = ['id', 'comment', 'user', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'comment', 'user', 'created_at', 'updated_at']




class ReviewLikeSerializer(serializers.ModelSerializer):
    """ReviewLike 모델 직렬화"""
    nickname = serializers.SerializerMethodField()

    class Meta:
        model = ReviewLike
        fields = ['id', 'review', 'user', 'nickname', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'review', 'user', 'created_at', 'updated_at']

    def get_nickname(self, obj):
        """유저 닉네임 반환 (유저가 없으면 '알수없음')"""
        return obj.user.nickname if obj.user else "알수없음"




class ReviewSerializer(serializers.ModelSerializer):
    """Review 모델 직렬화"""
    nickname = serializers.SerializerMethodField()  # 사용자 닉네임 반환
    comments = ReviewCommentSerializer(many=True, read_only=True)  # 연결된 댓글들
    total_likes = serializers.IntegerField(read_only=True)  # annotate로 계산된 값
    total_dislikes = serializers.IntegerField(read_only=True)  # annotate로 계산된 값

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'nickname', 'content', 'app_id', 'score', 'categories', 
            'created_at', 'updated_at', 'comments', 'total_likes', 'total_dislikes'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'comments', 'total_likes', 'total_dislikes'
        ]

    def get_nickname(self, obj):
        """유저 닉네임 반환 (유저가 없으면 '알수없음')"""
        return obj.user.nickname if obj.user else "알수없음"

    def validate_score(self, value):
        """
        평점 검증: 0.5~5.0 사이의 값만 허용하고, 0.5 단위로 작성되어야 함.
        """
        if not (0.5 <= value <= 5.0):
            raise serializers.ValidationError("평점은 0.5에서 5.0 사이의 값이어야 합니다.")
        if value * 10 % 5 != 0:
            raise serializers.ValidationError("평점은 0.5 단위로 작성되어야 합니다.")
        return value

