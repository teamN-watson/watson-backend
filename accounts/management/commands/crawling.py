from accounts.models import Tag

from django.core.management.base import BaseCommand
from django_seed import Seed
from accounts.models import Account, Interest, Tag
import environ
import requests


class Command(BaseCommand):
    help = "이 커맨드를 통해 태그 데이터를 만듭니다."

    def handle(self, *args, **options):
        env = environ.Env()
        api_key = env("STEAM_API_KEY")

        api_url = "https://api.steampowered.com/IStoreService/GetMostPopularTags/v1/"

        try:
            # 기본 파라미터 (영문 결과)
            params_en = {
                "key": api_key,
            }

            # 한글 결과를 위한 파라미터 추가
            params_ko = {"key": api_key, "language": "koreana"}

            response_en = requests.get(api_url, params=params_en)
            response_ko = requests.get(api_url, params=params_ko)

            # 요청 성공 여부 확인
            if response_en.status_code == 200 and response_ko.status_code == 200:
                data_en = response_en.json()  # 영문 데이터
                data_ko = response_ko.json()  # 한글 데이터

                data_en_dict = {
                    item["tagid"]: item["name"] for item in data_en["response"]["tags"]
                }
                data_ko_dict = {
                    item["tagid"]: item["name"] for item in data_ko["response"]["tags"]
                }

                for data in data_en["response"]["tags"]:
                    Tag.objects.get_or_create(
                        name_en=data_en_dict[data["tagid"]],
                        name_ko=data_ko_dict[data["tagid"]],
                        steam_tag_id=data["tagid"],
                    )

                self.stdout.write(self.style.SUCCESS(f"인기 태그 정보 생성 완료."))

        except requests.exceptions.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Error fetching data: {e}"))
