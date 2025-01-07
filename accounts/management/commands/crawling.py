from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import os
import django
from accounts.models import Tag

from django.core.management.base import BaseCommand
from django_seed import Seed
from accounts.models import Account, Interest, Tag


class Command(BaseCommand):
    help = "이 커맨드를 통해 태그 데이터를 만듭니다."

    def handle(self, *args, **options):
        # 브라우저 드라이버 설정
        driver = webdriver.Chrome()

        # 특정 URL에 연결하는 부분 (첫 페이지 열기)
        driver.get("https://store.steampowered.com/tag/browse/survival#global_1659")

        # 데이터 저장할 리스트
        category = []

        # 페이지 로딩 기다림 (필요 시 명시적으로 WebDriverWait 사용 가능)
        time.sleep(2)

        # 1) 우선 bbs_table_body를 갖는 요소(루트) 찾기
        root = driver.find_element(
            By.XPATH, "//div[@class='tag_browse_tags peeking_carousel']"
        )
        # 2) 그 안에서 class="tag_browse_tag"를 갖는 div 모두 찾기
        tag_divs = root.find_elements(By.XPATH, ".//div[@class='tag_browse_tag']")

        for div in tag_divs:
            # 태그 제목, 아이디 추출
            title = div.text
            tag_id = div.get_attribute("data-tagid")

            # 추출된 데이터 저장
            data = {"title": title, "tag_id": tag_id}

            Tag.objects.get_or_create(name=title, steam_tag_id=tag_id)

            category.append(data)

        driver.quit()

        # # JSON 파일로 저장
        # with open("category.json", "w", encoding="utf-8") as json_file:
        #     json.dump(category, json_file, ensure_ascii=False, indent=4)
