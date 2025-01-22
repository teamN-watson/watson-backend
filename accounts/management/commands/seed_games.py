import csv
from django.core.management.base import BaseCommand
from accounts.models import Game, Tag  # Game 모델 임포트
import ast

class Command(BaseCommand):
    help = "이 커맨드를 통해 CSV 파일의 데이터를 Game 모델에 적재합니다."

    def add_arguments(self, parser):
        # CSV 파일 경로를 받아오는 인자 추가
        parser.add_argument("file_path", type=str, help="CSV 파일의 경로")

    def handle(self, *args, **options):
        file_path = options["file_path"]  # CSV 파일 경로 가져오기

        try:
            # accounts_tag 데이터를 한 번만 조회하여 dict로 저장
            tags_dict = {tag.name_en: tag.name_ko for tag in Tag.objects.all()}

            with open(file_path, "r", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    # genres를 한글로 매핑
                    genres_english = eval(row["genres"])  # 문자열 -> 리스트 변환
                    genres_korean = [
                        tags_dict.get(genre, genre) for genre in genres_english
                    ]

                    # 데이터를 Game 모델에 저장
                    Game.objects.update_or_create(
                        appID=int(row['appID']),  # lookup field
                        defaults={  # 업데이트할 필드들
                            'name': row['name'],
                            'release_date': row['release_date'],
                            'required_age': int(row['required_age']) if row['required_age'] != '' else 0,
                            'price': float(row['price']) if row['price'] != '' else 0.0,
                            'header_image': row['header_image'],
                            'windows': row['windows'].lower() == 'true',
                            'mac': row['mac'].lower() == 'true',
                            'linux': row['linux'].lower() == 'true',
                            'metacritic_score': int(row['metacritic_score']) if row['metacritic_score'] != '' else 0,
                            'metacritic_url': row['metacritic_url'],
                            'supported_languages': eval(row["supported_languages"]),
                            'categories': eval(row['categories']) if row['categories'] else [],
                            'genres': ast.literal_eval(row["genres"]),
                            'genres_kr': genres_korean,
                            'screenshots': eval(row['screenshots']) if row['screenshots'] else [],
                            'movies': eval(row['movies']) if row['movies'] else [],
                            'estimated_owners': row['estimated_owners'],
                            'median_playtime_forever': int(row['median_playtime_forever']) if row['median_playtime_forever'] != '' else 0,
                            'tags': eval(row['tags']) if row['tags'] else {}
                        }
                    )
            
            self.stdout.write(
                self.style.SUCCESS("CSV 데이터를 성공적으로 적재했습니다.")
            )

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"파일을 찾을 수 없습니다: {file_path}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"오류 발생: {str(e)}"))