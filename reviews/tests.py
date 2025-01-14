from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Review


class ReviewSearchAPITest(APITestCase):
    """ReviewSearchAPIView 테스트"""

    @classmethod
    def setUpTestData(cls):
        """테스트 데이터 생성"""
        cls.review1 = Review.objects.create(
            content="Great action scenes in this game",
            categories=["action", "thriller"],
            app_id=101,
            game_name="Action Game"
        )
        cls.review2 = Review.objects.create(
            content="Epic RPG story with great characters",
            categories=["RPG", "adventure"],
            app_id=102,
            game_name="RPG Adventure"
        )
        cls.review3 = Review.objects.create(
            content="A casual puzzle game for relaxing",
            categories=["puzzle", "casual"],
            app_id=103,
            game_name="Casual Puzzle Game"
        )

    def test_search_with_exact_game_name(self):
        """게임 이름으로 정확히 검색 테스트"""
        response = self.client.get(reverse('reviews:review_search'), {'keyword': 'Action Game'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['game_name'], "Action Game")

    def test_search_with_partial_game_name(self):
        """게임 이름 일부로 검색 테스트"""
        response = self.client.get(reverse('reviews:review_search'), {'keyword': 'RPG'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['game_name'], "RPG Adventure")

    def test_search_with_review_content(self):
        """리뷰 내용으로 검색 테스트"""
        response = self.client.get(reverse('reviews:review_search'), {'keyword': 'relaxing'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['game_name'], "Casual Puzzle Game")

    def test_search_with_category(self):
        """카테고리로 검색 테스트"""
        response = self.client.get(reverse('reviews:review_search'), {'keyword': 'adventure'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['game_name'], "RPG Adventure")

    def test_search_with_nonexistent_keyword(self):
        """존재하지 않는 키워드로 검색 테스트"""
        response = self.client.get(reverse('reviews:review_search'), {'keyword': 'Nonexistent'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "검색 결과가 없습니다.")

    def test_search_without_keyword(self):
        """검색어 없이 요청한 경우"""
        response = self.client.get(reverse('reviews:review_search'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "검색어를 입력해주세요.")

    def test_search_with_special_characters(self):
        """특수 문자로 검색 테스트"""
        response = self.client.get(reverse('reviews:review_search'), {'keyword': '@#*!'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "검색 결과가 없습니다.")

    def test_search_case_insensitive(self):
        """대소문자 구분 없이 검색 테스트"""
        response = self.client.get(reverse('reviews:review_search'), {'keyword': 'action game'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['game_name'], "Action Game")

    def test_search_with_multiple_matches(self):
        """여러 결과가 매칭되는 경우"""
        response = self.client.get(reverse('reviews:review_search'), {'keyword': 'great'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 두 개의 리뷰가 매칭됨
        self.assertIn(self.review1.game_name, [review['game_name'] for review in response.data])
        self.assertIn(self.review2.game_name, [review['game_name'] for review in response.data])
