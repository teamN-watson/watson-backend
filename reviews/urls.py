from django.urls import path
from reviews import views

app_name = "reviews"

urlpatterns = [
    # 리뷰 목록 조회 및 생성
    path("", views.ReviewAPIView.as_view(), name="review_list"),  # /api/reviews/

    # 특정 리뷰 조회, 수정, 삭제
    path("<int:pk>/", views.ReviewDetailAPIView.as_view(), name="review_detail"),  # /api/reviews/<pk>/

    # 특정 리뷰에 댓글 생성
    path("<int:review_id>/comments/", views.ReviewCommentAPIView.as_view(), name="review_comment_create"),  # /api/reviews/<review_id>/comments/

    # 특정 댓글 수정 및 삭제
    path("comments/<int:pk>/", views.ReviewCommentDetailAPIView.as_view(), name="review_comment_detail"),  # /api/reviews/comments/<pk>/

    # 특정 리뷰에 좋아요/비추천 생성 및 상태 변경
    path("<int:review_id>/like/", views.ReviewLikeAPIView.as_view(), name="review_like"),  # /api/reviews/<review_id>/like/

    # 특정 댓글에 좋아요/비추천 생성 및 상태 변경
    path("comments/<int:comment_id>/like/", views.ReviewCommentLikeAPIView.as_view(), name="review_comment_like"),  # /api/reviews/comments/<comment_id>/like/

    # 리뷰 검색
    path("search/", views.ReviewSearchAPIView.as_view(), name="review_search"),  # /api/reviews/search/
    
    ]
