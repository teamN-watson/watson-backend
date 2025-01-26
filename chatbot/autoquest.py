from pydantic import BaseModel, Field
from dataclasses import dataclass
import os
from langchain_openai import ChatOpenAI
from typing import Literal, List
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
import requests
from bs4 import BeautifulSoup
from langchain.schema.runnable import Runnable, RunnableSequence
from langchain.schema import LLMResult, AIMessage, SystemMessage, HumanMessage
from accounts.models import SteamProfile, SteamReview, SteamPlaytime
from accounts.models import Tag, InterestTag, AccountInterest
from fake_useragent import UserAgent
from collections import defaultdict
import json
from collections import Counter
import random


@dataclass
class AssistantConfig:
    """
    Assistant의 설정을 관리하는 데이터 클래스

    Attributes:
        steam_api_key (str) : Steam API 접근을 위한 인증 키
        llm_model (str): 사용할 언어 모델의 이름 (예: gpt-4)
        temperature (float): 언어 모델의 창의성 조절 파라미터 (0.0 = 결정적, 1.0 = 창의적)
        not_supported_message (str): 게임 관련이 아닌 질문에 대한 기본 응답 메시지
    """
    steam_api_key: str
    llm_model: str
    temperature: float = 0.0
    not_result_message: str = "죄송합니다. 입력하신 정보와 관련된 게임을 찾을 수 없습니다. 🕵️"
    not_review_message: str = "리뷰가 없습니다. 🕵️"
    not_description_message: str = "설명이 없습니다. 🕵️"
    not_enough_message: str = "죄송합니다. 사용자의 취향을 분석할 수 있을 정도로 정보가 충분하지 않습니다. 🕵️"


class SummaryParser(BaseModel):
    """
    요약 모델의 출력 형태를 정의하는 Pydantic 모델
    """
    description: str = Field(
        description="게임에 대한 설명을 요약한 텍스트입니다",
        min_length=1,  # 최소 1글자 이상이어야 함
    )

    good_review: str = Field(
        description="게임을 추천하는 유저의 리뷰를 요약한 텍스트입니다",
        min_length=1,  # 최소 1글자 이상이어야 함
    )

    bad_review: str = Field(
        description="게임을 비추천하는 유저의 리뷰를 요약한 텍스트입니다",
        min_length=1,  # 최소 1글자 이상이어야 함
    )


# 커스텀 출력 파서
class ListOutputParser(Runnable):
    def invoke(self, input: AIMessage, config=None) -> List[int]:
        try:
            # AIMessage 객체에서 내용 추출
            text = input.content.strip()

            # 문자열을 리스트로 변환
            parsed_list = eval(text)
            if isinstance(parsed_list, list) and all(isinstance(x, int) for x in parsed_list):
                return parsed_list
            else:
                raise ValueError("Invalid list format")
        except Exception as e:
            print(f"Parsing error: {e}")
            return []


class AutoAssistant():
    """
    결과를 제공하는 통합 어시스턴트
    이 클래스는 사용자 질의를 처리하고 관련 게임 정보를 검색하는 핵심 기능을 제공
    """
    @classmethod
    def from_env(cls):
        """
        환경 변수에서 설정을 로드하여 인스턴스를 생성하는 클래스 메서드
        이 방식을 사용하면 설정을 코드와 분리하여 관리할 수 있음
        """
        config = AssistantConfig(
            steam_api_key=os.getenv("STEAM_API_KEY", ""),
            llm_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),  # 기본 모델 지정
            temperature=float(os.getenv("TEMPERATURE", "0.0")),  # 문자열을 float로 변환
        )
        return cls(config)

    def __init__(self, config: AssistantConfig):
        """
        Assistant 초기화
        모든 필요한 컴포넌트와 설정을 초기화
        사용자 입력이 어떤 도움을 원하는지 판단하는 함수
        """
        self.config = config
        self.restrict_id = [12095, 6650, 5611, 9130, 24904]

        # LangChain의 ChatOpenAI 모델 초기화
        self.llm = ChatOpenAI(
            temperature=config.temperature, model=config.llm_model)
        
        # JSON 출력 파서 설정
        self.summary_parser = JsonOutputParser(pydantic_object=SummaryParser)

        # 프롬프트 템플릿 설정
        self.summary_template = PromptTemplate(
            input_variables=["short_inform", "long_inform", "good_review", "bad_review"],
            partial_variables={
                "format_instructions": self.summary_parser.get_format_instructions()},
            template="""
            당신은 게임 관련 정보들을 한 눈에 깔끔하게 요약하는 도우미입니다.
            주어지는 입력 중 "짧은 게임 설명"은 해당 게임에 대한 핵심적인 설명, "긴 게임 설명"은 해당 게임에 대한 구체적인 설명을 의미합니다.
            또한, 주어지는 입력 중 "긍정적 게임 리뷰"는 해당 게임에 대해 긍정적인 평가를 내린 유저들의 의견, "부정적 게임 리뷰는 해당 게임에 대해 부정적인 평가를 내린 유저들의 의견을 의미합니다. 
            다양한 언어로 되어있는 리뷰이므로 내용을 먼저 이해한 뒤 진행하세요.
            "게임 짧은 설명"과 "게임 긴 설명"을 기반으로 게임에 대한 설명을 이해하기 쉽고 깔끔하게 최대 2문장으로 요약한 뒤, 한국어로 결과를 출력하세요.(게임 설명에 대한 요약 내용)
            또한, "게임 긍정적 리뷰"를 기반으로 유저들이 해당 게임에 느끼는 장점들을 이해하기 쉽고 깔끔하게 최대 2문장으로 요약한 뒤, 한국어로 결과를 출력하세요.(긍정적 리뷰에 대한 요약 내용)
            마지막으로 "게임 부정적 리뷰"를 기반으로 유저들이 해당 게임에 느끼는 단점들을 이해하기 쉽고 깔끔하게 최대 2문장으로 요약한 뒤, 한국어로 결과를 출력하세요.(부정적 리뷰에 대한 요약 내용)
            최대한 빠른 속도로 실행을 완료하세요.

            짧은 게임 설명:
            {short_inform}

            긴 게임 설명:
            {long_inform}

            긍정적 게임 리뷰:
            {good_review}

            부정적 게임 리뷰:
            {bad_review}

            {format_instructions}
            """
        )

        # 프롬프트 -> LLM -> 출력 파서로 이어지는 처리 파이프라인
        self.summarychain = RunnableSequence(
            first=self.summary_template,
            middle=[self.llm],
            last=self.summary_parser
        )

    def get_game_tag(self, app_id):
        """
        게임의 인기 태그 가져오는 함수
        """
        url = f"https://store.steampowered.com/app/{app_id}/"
        cookies = {
            'birthtime': '568022401',
            'lastagecheckage': '1-January-1990',
        }

        ua = UserAgent()
        headers = {
            "User-Agent": ua.random
        }

        response = requests.get(url, cookies=cookies, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # content_descriptors 찾기
        div = soup.find('div', class_='glance_tags popular_tags')

        # div 정보 없을 때 그냥 반환
        if not div:
            return div
        else:
            app_tags = div.find_all('a', class_='app_tag')

            # div는 있되 app_tag 없을 때 그냥 반환
            if not app_tags:
                return app_tags
            else:
                descriptors = [tag.text.strip() for tag in app_tags]
                tags = Tag.objects.filter(name_en__in=descriptors).values_list(
                    'steam_tag_id', flat=True)
                return tags

    def get_tagid(self, request):
        """
        사용자의 관심사 + 리뷰 + 플레이 타임 게임 태그 가져오는 함수
        """
        def get_interest(user_id):
            """
            관심사 가져오기 - interest_id 별로 그룹화된 Tag 결과 반환
            """
            # AccountInterest에서 사용자의 interest_id 가져오기
            interest_ids = AccountInterest.objects.filter(
                account_id=user_id
            ).values_list('interest_id', flat=True)

            # InterestTag에서 각 interest_id에 연결된 tag_id 가져오기
            interest_tags = InterestTag.objects.filter(
                interest_id__in=interest_ids
            ).values_list('interest_id', 'tag_id')

            # 태그 ID와 steam_tag_id 가져오기
            tag_data = Tag.objects.filter(
                id__in=[tag_id for _, tag_id in interest_tags]
            ).values_list('id', 'steam_tag_id')

            # 태그 ID를 딕셔너리로 매핑
            tag_dict = {tag_id: steam_tag_id for tag_id,
                        steam_tag_id in tag_data}

            # interest_id 별로 그룹화된 결과 생성
            grouped_result = defaultdict(list)
            for interest_id, tag_id in interest_tags:
                if tag_id in tag_dict:
                    grouped_result[interest_id].append(tag_dict[tag_id])

            # 리스트의 리스트 형태로 반환
            return list(grouped_result.values())

        # 스팀 연동된 유저인지 확인
        if request.user.steamId:
            # 리뷰 쓴 유저일 때
            if SteamProfile.objects.filter(account_id=request.user.id, is_review=1).exists():
                tag_id = get_interest(request.user.id)
                app_id = SteamReview.objects.filter(
                    account_id=request.user.id).values_list('app_id', flat=True)
                for i in app_id:
                    game_tag = self.get_game_tag(i)
                    if game_tag:
                        tag_id.append(list(game_tag))

            # 리뷰 안 썼지만 플레이 타임 정보 있는 유저일 때
            elif SteamProfile.objects.filter(account_id=request.user.id, is_playtime=1).exists():
                tag_id = get_interest(request.user.id)
                app_id = SteamPlaytime.objects.filter(
                    account_id=request.user.id).values_list('app_id', flat=True)
                for i in app_id:
                    game_tag = self.get_game_tag(i)
                    if game_tag:
                        tag_id.append(list(game_tag))
            else:
                tag_id = get_interest(request.user.id)
        else:
            tag_id = get_interest(request.user.id)
        return tag_id


    def search_filter(self, request, tags, user_game):
        """
        태그를 통한 게임 검색 진행
        """
        tags_str = ",".join(map(str, tags))
        url = f'https://store.steampowered.com/search/?ignore_preferences=1&tags={tags_str}&ndl=1'

        # User-Agent 설정
        ua = UserAgent()
        headers = {
            "User-Agent": ua.random
        }

        # HTTP GET 요청 및 파싱
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # id가 'search_resultsRows'인 div 찾기
        container = soup.find('div', id='search_resultsRows')

        # 'search_resultsRows' 안에 있는 직계 <a> 태그들을 최대 50개까지 가져오기
        links = container.find_all(
            'a', recursive=False, limit=50) if container else []

        # 결과 아무것도 없으면 바로 안내 문구 반환
        if not links:
            return self.config.not_result_message

        # 각 <a> 태그에서 data-ds-appid 속성 추출
        app_ids = []
        count = 0
        random_links = random.sample(links, len(links))
        for link in random_links:
            tagids = link.get('data-ds-tagids')
            appid = link.get('data-ds-appid')

            # 인기 태그 정보 없을 때, 번들과 같이 appid가 없는 대상일 경우 스킵
            if not tagids or not appid:
                continue

            # 사용자가 플레이 했던 게임, 이미 검색된 게임은 제외
            if appid not in user_game and appid not in app_ids:
                # 미성년자일 때 검색 결과 필터링
                if request.user.age < 20:
                    if not any(tag in json.loads(tagids) for tag in self.restrict_id):
                        app_ids.append(appid)
                        count += 1
                else:
                    app_ids.append(appid)
                    count += 1

            # 수집된 결과 3개 채워졌으면 반복문 탈출
            if count == 3:
                break

        # app_id가 아무것도 모이지 않았을 때 안내 문구 반환
        if not app_ids:
            return self.config.not_result_message
        return app_ids


    def get_game_info(self, game_id):
        """
        스팀 상세 페이지 내의 게임 설명 추출
        """
        url = f'https://store.steampowered.com/app/{game_id}/'

        cookies = {
            'birthtime': '568022401',
            'lastagecheckage': '1-January-1990',
        }

        ua = UserAgent()
        headers = {
            "User-Agent": ua.random
        }

        response = requests.get(url, cookies=cookies, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 짧은 설명, 긴 설명 둘 다 추출
        try:
            short_inform = soup.find(
                'div', class_='game_description_snippet').get_text(strip=True)
        except:
            short_inform = "짧은 설명이 없습니다"
        try:
            long_inform = soup.find(
                'div', id='game_area_description').get_text(strip=True)
        except:
            long_inform = "긴 설명이 없습니다."
        title_text = soup.find('div', id='appHubAppName')
        game_title = title_text.text.strip() if title_text else "Unknown Title"
        game_image = soup.find('img', class_='game_header_image_full')[
            'src'] if soup.find('img', class_='game_header_image_full') else None

        # 태그에서 텍스트만 추출
        if not short_inform:
            short_inform = self.config.not_description_message

        # 태그에서 텍스트만 추출
        if not long_inform:
            long_inform = self.config.not_description_message

        inform = {
            "short_inform": short_inform,
            "long_inform": long_inform
        }

        game = {
            "steam_app_id": game_id,
            "title": game_title,
            "image": game_image,
        }
        return inform, game


    def search_game_review(self, base_url, cursor):
        """
        Steam API로 리뷰 데이터 수집 (유용한 순, 100일 이내, 최대 100개)
        """
        reviews = []
        for i in range(0, 1):
            # URL 업데이트
            url = base_url.format(cursor=cursor)

            # API 호출
            response = requests.get(url)
            data = response.json()

            # 리뷰 수집
            if 'reviews' in data:  # 리뷰가 있는 경우에만 실행
                for review in data['reviews']:
                    reviews.append(review['review'])

            # 다음 페이지의 cursor 값 가져오기
            cursor = data['cursor']

            if not reviews:
                return self.config.not_review_message

            # 리뷰가 더 없으면 종료
            if not cursor or len(data['reviews']) == 0:
                break

        return reviews


    def get_game_review(self, appid):
        """
        긍정, 부정 별로 최근 유용한 리뷰 100개 요약 내용 추출하는 함수
        """
        cursor = 'cursor=*'
        good_review_api = f"https://store.steampowered.com/appreviews/{appid}?json=1&filter=all&day_range=100&review_type=positive&num_per_page=100&{cursor}"
        bad_review_api = f"https://store.steampowered.com/appreviews/{appid}?json=1&filter=all&day_range=100&review_type=negative&num_per_page=100&{cursor}"

        good_review = self.search_game_review(good_review_api, cursor)
        bad_review = self.search_game_review(bad_review_api, cursor)

        review = {
            "good_review": good_review,
            "bad_review": bad_review,
        }
        return review


    def find_game_id(self, request):
        """
        특정 계정에서 플레이 한 게임 아이디 가져오는 함수
        """
        # 스팀 연동된 유저인지 확인
        if request.user.steamId:
            # 리뷰 쓴 유저일 때
            if SteamProfile.objects.filter(account_id=request.user.id, is_review=1).exists():
                app_id = SteamReview.objects.filter(
                    account_id=request.user.id).values_list('app_id', flat=True)

            # 리뷰 안 썼지만 플레이 타임 정보 있는 유저일 때
            elif SteamProfile.objects.filter(account_id=request.user.id, is_playtime=1).exists():
                app_id = SteamPlaytime.objects.filter(
                    account_id=request.user.id).values_list('app_id', flat=True)

            else:
                return []
        else:
            return []
        return list(app_id)
    
    
    def final_tag(self, request):
        """
        검색에 사용할 사용자 관심사 태그 추출하는 함수
        """
        user_interest = self.get_tagid(request)

        # 리스트 평탄화
        flattened = sum(user_interest, [])

        counts = Counter(flattened)

        # 등장 횟수가 가장 많은 (원소, 횟수) 한 쌍을 반환함
        top1_count = counts.most_common(1)[0][1]
        if top1_count != 1:
            # 가장 많이 등장한 횟수가 1이 아닐 경우에만 상위 3개를 뽑음
            top_3 = [elem for elem, cnt in counts.most_common(3)]
            return top_3
        else:
            return []


    def search_game(self, request):
        """
        게임 추천 원할 시 검색 결과 가져오는 최종 함수
        """
        # 사용자가 보유하는 게임 아이디 추출
        user_game = self.find_game_id(request)

        # 사용자의 취향을 분석한 태그 추출
        user_tag = self.final_tag(request)

        if not user_tag:
            return {"message": self.config.not_enough_message}

        # 실제 검색에 사용할 게임 아이디 추출
        search_game_id = self.search_filter(
            request, user_tag, user_game)

        # 검색 결과로 아무런 게임이 없을 때 바로 안내 문구로 결과 출력
        if search_game_id == self.config.not_result_message or not search_game_id[0]:
            return {"message": self.config.not_result_message}

        # 게임 설명 요약 정보
        game_information = {
            "message": "다음과 같은 게임을 추천드립니다. 🕵️", "game_data": []}
        for id in search_game_id[0:3]:
            if id:
                game_info, game_data = self.get_game_info(id)
                game_review = self.get_game_review(id)
                # LLM 호출
                game_summary = self.summarychain.invoke({
                    "short_inform": game_info['short_inform'],
                    "long_inform": game_info['long_inform'],
                    "good_review": game_review['good_review'],
                    "bad_review": game_review['bad_review']
                })

                if game_summary:
                    game_data['description'] = game_summary['description']
                    game_data['good_review'] = game_summary['good_review']
                    game_data['bad_review'] = game_summary['bad_review']
                    game_information["game_data"].append(game_data)

        return game_information


    def process_query(self, request):
        """
        사용자 질문을 처리하고 적절한 응답을 생성하는 메인 메서드
        """
        try:
            return self.search_game(request)

        except Exception as e:
            print(e)
            return {"message": self.config.not_result_message}