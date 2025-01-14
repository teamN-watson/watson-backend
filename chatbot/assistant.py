from pydantic import BaseModel, Field
from dataclasses import dataclass
import os
from langchain_openai import ChatOpenAI
from typing import Literal
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
import requests
import re
from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from accounts.models import SteamProfile, SteamReview, SteamPlaytime
from accounts.models import Tag, InterestTag, AccountInterest
from fake_useragent import UserAgent
from collections import defaultdict
import json




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
    steam_api_key : str
    llm_model: str
    temperature: float = 0.0
    not_supported_message: str = "죄송합니다. 게임과 관련 질문에 대해서만 응답을 제공할 수 있습니다. 😿"
    restrict_message: str = "죄송합니다. 관련 게임은 성인 연령만 검색 가능합니다. 😿"
    not_result_message: str = "죄송합니다. 입력하신 정보와 관련된 게임을 찾을 수 없습니다. 😿"
    not_find_message: str = "죄송합니다. 원활한 검색을 위해 게임 제목을 영어로 정확하게 입력해주세요. 😿"
    not_review_message: str = "리뷰가 없습니다. 😿"
    not_description_message: str = "설명이 없습니다. 😿"


class AgentAction(BaseModel):
    """
    에이전트의 행동을 정의하는 Pydantic 모델
    """
    # Literal을 사용하여 action 필드가 가질 수 있는 값을 제한합니다
    action: Literal["search_game","search_game_info", "not_supported"] = Field(
        description="에이전트가 수행할 행동의 타입을 지정합니다",
    )

    action_output: str = Field(
        description="사용자가 입력에 기반한 핵심 텍스트입니다",
        min_length=1,  # 최소 1글자 이상이어야 함
    )

class Assistant():
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
            steam_api_key=os.getenv("STEAM_API_KEY",""),
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
        self.agent_parser = JsonOutputParser(pydantic_object=AgentAction)

        # 프롬프트 템플릿 설정
        # 이 템플릿은 AI가 질의를 어떻게 처리할지 지시합니다
        self.agent_prompt = PromptTemplate(
            input_variables=["input"],  # 템플릿에서 사용할 변수들
            partial_variables={
                "format_instructions": self.agent_parser.get_format_instructions()},
            template="""
            당신은 게임 관련 정보를 검색하는 도우미입니다.
            입력된 질의가 게임 관련 내용인지 확인하세요.

            # 게임 관련 주제 판단 기준:
            - 질의에 게임(콘솔 게임) 제목/장르/특징 등이 포함되어 있는지
            - 게임 장르(액션, RPG, 재밌는, 귀여운 등)에 관한 내용이 포함되어 있는지
            - "게임"이라는 단어가 포함되어 있는지

            ## Action 결정 규칙
            1. `search_game_info`
            - 사용자가 “특정 게임에 대한 상세정보”를 요청하는 경우  
            - 예: “어쌔신 크리드 오디세이에 대해 알려줘”, “GTA 게임에 대해 알려줘” 등

            2. `search_game`
            - 사용자가 “게임을 추천해 달라거나, 특정 조건에 맞는 게임을 찾아달라” 등  
            - 예: “귀여운 동물 나오는 힐링 게임 뭐 있어?”, “RPG 추천해줘”

            3. `not_supported`
            - 게임과 전혀 무관하거나, 지원하지 않는 주제(음식, 여행, 의료 등).  
            - 예: “파스타 레시피 알려줘”, “병원 진료 예약 좀” 등
            - 게임과 관련되었어도 핵심 주제어(게임 이름)을 파악하지 못할 경우

            # Action이 'not_supported'인 경우:
            - action_output은 빈 문자열로 설정

            # Action이 'search_game_info'인 경우:
                1. action을 "search_game_info"로 설정
                2. 검색어 최적화:
                    - 핵심 주제어(특정 게임이름) 추출
                    - 불필요한 단어 제거 (찾아줘, 알려줘 등)
                    - 맥락 상 특정한 게임 이름은 그대로 유지
                    - 핵심 주제어(특정 게임이름)가 여러가지일 시 가장 먼저 인식되는 주제어(게임 이름)로 추출

            # Action이 'search_game'인 경우:
                1. action을 "search_game"로 설정
                2. 검색어 최적화:
                    - 사용자가 입력한 내용에서 변형 없이 그대로 유지

            분석할 질의: {input}

            {format_instructions}""")

        # 실행 체인 생성
        # 프롬프트 -> LLM -> 출력 파서로 이어지는 처리 파이프라인
        self.chain = RunnableSequence(
            first=self.agent_prompt,
            middle=[self.llm],
            last=self.agent_parser
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
                tags = Tag.objects.filter(name_en__in=descriptors).values_list('steam_tag_id', flat=True)
                return tags

    def search_tag(self, request, query):
        """
        실제 검색하고자 하는 태그 추출 (관심사, 스팀 데이터 반영)
        """

        def input_tag(self, user_input):
            """
            사용자 입력으로부터 태그 추출하는 함수
            """
            # 프롬프트 설정
            input_prompt = """
            당신은 주어진 사용자 입력에서 키워드를 추출하고, 그 키워드(또는 그 키워드와 의미가 유사한 단어)가
            태그 사전(tag)에 들어있는 name_ko와 부분 일치 혹은 유의미하게 관련이 있다면 그 태그를 최대 3개까지 추출하시오.
            반드시 주어진 태그 사전에 존재하는 태그로 추출하시오.

            # 단계별 지침
            1. 사용자 입력에서 핵심 키워드를 골라내시오.
            - 예시) "농사짓고 낚시하는 힐링 게임 추천해줘"라는 입력이 들어올 때 -> ["농사", "낚시", "힐링"] 키워드 추출
            2. tag 배열에 들어있는 tag 객체들의 name_ko(한글 태그명)와 해당 키워드를 비교하여,
            - 완전 일치(동일 단어)가 있으면 우선적으로 선택.
            - 부분 일치나 유의미하게 유사(예시: "농사"키워드가 있을 때 "농장"나 "농업" 등, "낚시"와 "낚시질"와 "물고기" 등)가 있으면 그 태그를 선택.
            - 전혀 관련이 없으면 선택하지 말기.
            3. 최종적으로 최대 3개의 태그를 골라서, 아래 형식 그대로 출력하시오.
            4. 출력은 최종적으로 선택된 태그들만 출력하시오.


            # 응답 형식
            - 반드시 아래 파이썬 list 객체 형태로만 응답하시오.  
            - **트리플 백틱(```)이나 코드블록, 추가 설명 문장 등은 절대 포함하지 마시오.**  
            - name_ko 제외한 steam_tag_id만 출력하시오.
            - 응답 예시(만약 태그가 2개라면):
            [첫번째 태그 번호, 두번째 태그 번호]

            # 중요 규칙
            - 주어진 태그 사전(tag)에 실제로 존재하는 name_ko 값만 사용하시오.
            - 최대 3개까지만 응답. 0개여도 좋음.
            - 사용자가 원하지 않은 (무관한) 태그는 절대 포함하지 마시오.
            - 최종적으로 선택된 태그에 대한 정보만 추출하시오.
            - 한글이 아닌 name_ko는 무시해도 좋음(또는 필요시 부분일치).
            """

            # Django 모델 객체를 리스트로 변환
            tags = list(Tag.objects.values("name_ko", "steam_tag_id"))

            # 메시지 생성
            messages = [
                {"role": "system", "content": input_prompt},
                {"role": "user", "content": f"사용자 입력:\n{user_input}\n\ntag:\n{tags}"}
            ]

            # LLM 호출
            response = self.llm.invoke(messages)
            return response.content
            
        input_tag = input_tag(self, query)

        # 사용자 입력에서 아무런 결과도 출력되지 않을 때 안내 문구 반환
        if input_tag:
            input_tag = json.loads(input_tag)
        else:
            return self.config.not_result_message

        # 미성년자의 경우 검색어 필터링
        if request.user.age < 20:
            if any(tag in input_tag for tag in self.restrict_id):
                return self.config.restrict_message

        def get_interest(request):
            """
            관심사 가져오기 - interest_id 별로 그룹화된 Tag 결과 반환
            """
            # AccountInterest에서 사용자의 interest_id 가져오기
            interest_ids = AccountInterest.objects.filter(
                account_id=request.user.id
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
            tag_dict = {tag_id: steam_tag_id for tag_id, steam_tag_id in tag_data}

            # interest_id 별로 그룹화된 결과 생성
            grouped_result = defaultdict(list)
            for interest_id, tag_id in interest_tags:
                if tag_id in tag_dict:
                    grouped_result[interest_id].append(tag_dict[tag_id])

            # 리스트의 리스트 형태로 반환
            return list(grouped_result.values())
        
        
        def find_similar_tags(self, interest_tag, input):
            """
            사용자 입력 + 관심사 정보 모두 고려한 실제 검색 결과 추출 AI 모델
            """
            # 프롬프트 설정
            similar_prompt = """
            당신은 게임 태그 분석 도우미입니다.
            주어지는 입력 중 "사용자 입력"은 사용자가 원하는 장르, "관심사 태그"는 사용자가 평소에 좋아하던 게임에 대한 특징을 의미하는 태그 정보입니다.
            "관심사 태그"는 게임 별로 여러 그룹으로 나뉘어있는 정보입니다. 
            주어진 사용자 입력과 사용자 관심사 태그를 바탕으로, 여러 그룹 중 사용자가 원하는 장르와 연관이 있는 게임이 있는지 먼저 찾습니다.
            연관이 있는 게임을 먼저 찾은 뒤, 사용자 입력을 고려하여 앞서 찾은 연관된 게임의 비장르적 특징 (ex, 분위기 있는, 다채로운, 귀여운 등)을 최대 3개 추출합니다.
            만일 연관된 게임이 전혀 없었다면 사용자 입력에 연관성이 높거나 분위기가 비슷한 게임 내 비장르적 특징 태그(steam_tag_id)를 추론합니다.
            추론할 특징 태그는 반드시 주어진 관심사 태그 안에 있는 태그로 추론합니다.

            주어진 정보:
            - 사용자 입력: (예: "총 쏘고 경쟁하는 게임 추천해줘")
            - 사용자 관심사 태그: (예: ["귀여운", "힐링"])
            - 각 태그는 게임의 특정 특징이나 분위기를 나타냅니다.

            작업 지침:
            - 주어진 사용자 입력과 관심사 태그의 의미를 해석합니다.
            - 선택된 태그들은 실제로 함께 쓰일 가능성이 높은, 논리적이고 의미 있는 연관성을 가져야 합니다.
            - 연관있는 태그가 없을 시 아무런 결과도 반환하지 않아도 됨
            - 반드시 주어진 관심사 태그에 있는 태그로 추출해야 합니다.
            - "인디", "캐주얼"은 직접적인 언급이 있지 않은 이상 포함하지 마시오.
            - 게임과 일반적으로 연관있는 태그들은 사용자가 직접적으로 언급하지 않는 이상 포함하지 마시오. (예. 게임-이스포츠)

            제한 사항:
            - 게임 장르 태그(MOBA, RPG, 스포츠, 액션 등)는 제외합니다.
            - 결과는 steam_tag_id만을 포함한 리스트여야 합니다.
            - 최대 3개의 태그를 추출하며, 상황에 따라 3개 미만일 수 있습니다.

            응답 형식 예시: [492, 649, 3582]
            """

            # 메시지 생성
            messages = [
                {"role": "system", "content": similar_prompt},
                {"role": "user", "content": f"관심사 태그:\n{interest_tag}\n\n사용자 입력:\n{input}"}
            ]

            # LLM 호출
            response = self.llm.invoke(messages)

            return response.content
        
        # 스팀 연동된 유저인지 확인
        if request.user.steamId:
            # 리뷰 쓴 유저일 때
            if SteamProfile.objects.filter(account_id=request.user.id, is_review=1).exists(): 
                tag_id = get_interest(request)
                app_id = SteamReview.objects.filter(
                    account_id=request.user.id).values_list('app_id', flat=True)
                for i in app_id:
                    game_tag = self.get_game_tag(i)
                    if game_tag:
                        tag_id.append(game_tag)
            
            # 리뷰 안 썼지만 플레이 타임 정보 있는 유저일 때
            elif SteamProfile.objects.filter(account_id=request.user.id, is_playtime=1).exists(): 
                tag_id = get_interest(request)
                app_id = SteamPlaytime.objects.filter(
                    account_id=request.user.id).values_list('app_id', flat=True)
                for i in app_id:
                    game_tag = self.get_game_tag(i)
                    if game_tag:
                        tag_id.append(game_tag)
            else:
                tag_id = get_interest(request)
        else:
            tag_id = get_interest(request)

        tags = []
        for group in tag_id:
            # 각 그룹(tag_id 리스트)별로 쿼리 실행
            tag_group = list(Tag.objects.filter(steam_tag_id__in=group).values(
                'name_ko', 'steam_tag_id'
            ))
            tags.append(tag_group)
        
        # 관심사 태그와 사용자 입력과 연관지을 수 있는 태그 추출
        found_tag = find_similar_tags(self, query, tags)
        if found_tag:
            found_tag_list = json.loads(found_tag)
            return input_tag, list(set(input_tag + found_tag_list))
        else:
            return input_tag, input_tag


    def search_filter(self, request, tags, input_tag):
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

        # 'search_resultsRows' 안에 있는 직계 <a> 태그들을 최대 10개까지 가져오기
        links = container.find_all('a', recursive=False, limit=10) if container else []

        # 결과 아무것도 없으면 바로 안내 문구 반환
        if not links:
            return self.config.not_result_message

        # 각 <a> 태그에서 data-ds-appid 속성 추출
        app_ids = []
        sub_link = []
        count = 0
        for link in links: 
            tagids = link.get('data-ds-tagids')
            appid = link.get('data-ds-appid')

            # 인기 태그 정보 없을 때, 번들과 같이 appid가 없는 대상일 경우 스킵
            if not tagids or not appid:
                continue

            # 사용자 입력과 크게 연관 없을 때 예비 용으로 저장 후 일단 스킵
            if not any(tag in json.loads(tagids) for tag in input_tag):
                sub_link.append(link)
                continue

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

        if count < 3:
            for link in sub_link: 
                tagids = link.get('data-ds-tagids')
                appid = link.get('data-ds-appid')

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
            short_inform = soup.find('div', class_='game_description_snippet').get_text(strip=True)
        except:
            short_inform = "짧은 설명이 없습니다"
        try:
            long_inform = soup.find(
                'div', id='game_area_description').get_text(strip=True)
        except:
            long_inform = "긴 설명이 없습니다."
        title_text = soup.find('div', id='appHubAppName')
        game_title = title_text.text.strip() if title_text else "Unknown Title"
        game_image = soup.find('img', class_='game_header_image_full')['src'] if soup.find('img', class_='game_header_image_full') else None


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
        Steam API로 리뷰 데이터 수집 (유용한 순, 약 5달 이내, 최대 100개)
        """
        reviews = []
        for i in range(0,1):
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
        good_review_api = f"https://store.steampowered.com/appreviews/{appid}?json=1&filter=all&day_range=150&review_type=positive&num_per_page=100&{cursor}"
        bad_review_api = f"https://store.steampowered.com/appreviews/{appid}?json=1&filter=all&day_range=150&review_type=negative&num_per_page=100&{cursor}"

        good_review = self.search_game_review(good_review_api, cursor)
        bad_review = self.search_game_review(bad_review_api, cursor)

        review = {
            "good_review" : good_review,
            "bad_review" : bad_review,
        }
        return review
    
    def get_summary(self, game_info, game_review):
        """
        게임 관련 요약하는 AI 모델
        """
        prompt = """
        당신은 게임 관련 정보들을 한 눈에 깔끔하게 요약하는 도우미입니다.
        주어지는 입력 중 "게임 짧은 설명"은 해당 게임에 대한 핵심적인 설명, "게임 긴 설명"은 해당 게임에 대한 구체적인 설명을 의미합니다.
        또한, 주어지는 입력 중 "게임 긍정적 리뷰"는 해당 게임에 대해 긍정적인 평가를 내린 유저들의 의견, "게임 부정적 리뷰는 해당 게임에 대해 부정적인 평가를 내린 유저들의 의견을 의미합니다. 
        다양한 언어로 되어있는 리뷰이므로 내용을 먼저 이해한 뒤 진행하세요.
        "게임 짧은 설명"과 "게임 긴 설명"을 기반으로 게임에 대한 설명을 이해하기 쉽고 깔끔하게 최대 3문장으로 요약한 뒤, 한국어로 결과를 출력하세요.(게임 설명에 대한 요약 내용)
        또한, "게임 긍정적 리뷰"를 기반으로 유저들이 해당 게임에 느끼는 장점들을 이해하기 쉽고 깔끔하게 최대 3문장으로 요약한 뒤, 한국어로 결과를 출력하세요.(긍정적 리뷰에 대한 요약 내용)
        마지막으로 "게임 부정적 리뷰"를 기반으로 유저들이 해당 게임에 느끼는 단점들을 이해하기 쉽고 깔끔하게 최대 3문장으로 요약한 뒤, 한국어로 결과를 출력하세요.(부정적 리뷰에 대한 요약 내용)
        최대한 빠른 속도로 실행을 완료하세요.

        # 입력 형식 : ```json, ``` 이러한 기호는 절대 포함하지 마시오.
        {
            "description": 게임 설명에 대한 요약 내용,
            "good_review": 긍정적 리뷰에 대한 요약 내용,
            "bad_review": 부정적 리뷰에 대한 요약 내용
        }
        """

        # 메시지 생성
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user",
                "content": f"게임 짧은 설명:\n{game_info['short_inform']}\n\게임 긴 설명:\n{game_info['long_inform']}\n\게임 긍정적 리뷰:{game_review['good_review']}\n\게임 부정적 리뷰:{game_review['bad_review']}"}
        ]

        # LLM 호출
        response = self.llm.invoke(messages)

        return response.content


    def search_game(self, request, query):
        """
        게임 추천 원할 시 검색 결과 가져오는 최종 함수
        """
        # 사용자 입력으로부터 관련 태그 추출
        input_tag, search_tag = self.search_tag(request, query)
        
        # 입력 내용 인식이 어렵거나 유저가 미성년자라 입력 내용이 부적절할 때 바로 안내 문구로 결과 출력
        if search_tag == self.config.not_result_message or search_tag == self.config.restrict_message:
            return {"message":search_tag}

        # 실제 검색에 사용할 게임 아이디 추출
        search_game_id = self.search_filter(request, search_tag, input_tag)

        # 검색 결과로 아무런 게임이 없을 때 바로 안내 문구로 결과 출력
        if search_game_id == self.config.not_result_message or not search_game_id[0]:
            return {"message": self.config.not_result_message}
        
        # 게임 설명 요약 정보
        game_information = {"message": "다음과 같은 게임을 추천드립니다. 😸","game_data": []}
        for id in search_game_id:
            if id:
                game_info, game_data = self.get_game_info(id)
                game_review = self.get_game_review(id)
                game_summary = self.get_summary(game_info, game_review)

                if game_summary:
                    game_summary = json.loads(game_summary)

                    game_data['description'] = game_summary['description']
                    game_data['good_review'] = game_summary['good_review']
                    game_data['bad_review'] = game_summary['bad_review']
                    game_information["game_data"].append(game_data)

        return game_information


    def search_game_info(self, request, query):
        """
        특정 게임에 대한 정보 원할 시 결과 추출
        """
        
        # 모델에서 제대로 키워드를 추출하지 못했을 경우 안내 문장 반환
        if not query:
            return {"message":self.config.not_result_message}
        
        def search_game_name(query):
            """
            추출된 게임 이름으로 가장 먼저 검색되는 게임 아이디 추출
            """
            url = f"https://store.steampowered.com/search/?ignore_preferences=1&term={query}&ndl=1"

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

            # 'search_resultsRows' 안에 있는 직계 <a> 태그 최대 10개 가져오기
            links = container.find_all('a', recursive=False, limit=10) if container else []
            
            # 결과 아무것도 없으면 바로 안내 문구 반환
            if not links:
                return self.config.not_find_message

            # 각 <a> 태그에서 data-ds-appid 속성 추출
            app_ids = []
            count = 0
            for link in links: 
                appid = link.get('data-ds-appid')

                # 번들과 같이 appid가 없는 대상일 경우 스킵
                if not appid:
                    continue

                # 미성년자일 때 검색 결과 필터링
                if request.user.age < 20:
                    tagids = link.get('data-ds-tagids')
                    
                    # 인기 태그 정보 없을 때 스킵
                    if not tagids:
                        continue

                    if not any(tag in json.loads(tagids) for tag in self.restrict_id):
                        app_ids.append(appid) 
                        count += 1
                    else:
                        return self.config.restrict_message
                else:
                    app_ids.append(appid)
                    count += 1
                
                # 수집된 결과 1개 채워졌으면 반복문 탈출
                if count == 1:
                    break

            # app_id가 아무것도 모이지 않았을 때 안내 문구 반환
            if not app_ids:
                return self.config.not_find_message
            
            return app_ids

        # 사용자가 검색하고자 하는 게임의 id 추출
        game_id = search_game_name(query)
        
        if game_id == self.config.not_find_message or game_id == self.config.restrict_message:
            return {"message": game_id}

        # 게임 설명 요약 정보
        game_information = {"message": "검색하신 게임에 대한 정보입니다. 😸", "game_data": []}
        game_info, game_data = self.get_game_info(game_id)
        game_review = self.get_game_review(game_id)
        game_summary = self.get_summary(game_info, game_review)

        if game_summary:
            game_summary = json.loads(game_summary)
            game_data['description'] = game_summary['description']
            game_data['good_review'] = game_summary['good_review']
            game_data['bad_review'] = game_summary['bad_review']
            game_information["game_data"].append(game_data)

        return game_information


    def process_query(self, request, query: str):
        """
        사용자 질문을 처리하고 적절한 응답을 생성하는 메인 메서드
        """
        try:
            result = self.chain.invoke({"input": query})

            # 분석 결과에서 필요한 정보 추출
            action = result["action"]  # 수행할 액션
            action_output = result["action_output"]  # 추출된 사용자 입력

            # 게임 관련 질의가 아닌 경우 지원하지 않는다는 메시지 반환
            if action == "not_supported":
                return {"message":self.config.not_supported_message}

            # 게임 관련 질의인 경우 분기 처리
            # 게임 추천 액션 사용하는 경우
            if action == "search_game":
                return self.search_game(request, action_output)
            
            elif action == "search_game_info":
                return self.search_game_info(request, action_output)

        except Exception as e:
            return {"message":self.config.not_result_message}