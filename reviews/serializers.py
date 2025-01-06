from rest_framework import serializers
from .models import Review, ReviewComment, ReviewLike

class ReviewCommentSerializer(serializers.ModelSerializer):
    """ReviewComment 모델 직렬화"""
    nickname = serializers.SerializerMethodField()

    class Meta:
        model = ReviewComment
        fields = ['id', 'review', 'user', 'nickname', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_nickname(self, obj):
        """유저 닉네임 반환 (유저가 없으면 '알수없음')"""
        return obj.user.nickname if obj.user else "알수없음"


class ReviewLikeSerializer(serializers.ModelSerializer):
    """ReviewLike 모델 직렬화"""
    nickname = serializers.SerializerMethodField()

    class Meta:
        model = ReviewLike
        fields = ['id', 'review', 'user', 'nickname', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_nickname(self, obj):
        """유저 닉네임 반환 (유저가 없으면 '알수없음')"""
        return obj.user.nickname if obj.user else "알수없음"


class ReviewSerializer(serializers.ModelSerializer):
    """Review 모델 직렬화"""
    nickname = serializers.SerializerMethodField()
    comments = ReviewCommentSerializer(many=True, read_only=True)  # 연결된 댓글들
    total_likes = serializers.SerializerMethodField()
    total_dislikes = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'user', 'nickname', 'content', 'app_id', 'score', 'created_at', 'updated_at', 'comments', 'total_likes', 'total_dislikes']
        read_only_fields = ['id', 'created_at', 'updated_at', 'comments', 'total_likes', 'total_dislikes']

    def get_nickname(self, obj):
        """유저 닉네임 반환 (유저가 없으면 '알수없음')"""
        return obj.user.nickname if obj.user else "알수없음"

    def get_total_likes(self, obj):
        """총 좋아요(추천) 수 반환"""
        return obj.likes.filter(is_active=1).count()

    def get_total_dislikes(self, obj):
        """총 비추천 수 반환"""
        return obj.likes.filter(is_active=-1).count()
