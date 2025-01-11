import csv
from django.core.management.base import BaseCommand
from accounts.models import Game  # Game 모델 임포트

class Command(BaseCommand):
    help = "이 커맨드를 통해 CSV 파일의 데이터를 Game 모델에 적재합니다."

    def add_arguments(self, parser):
        # CSV 파일 경로를 받아오는 인자 추가
        parser.add_argument('file_path', type=str, help='CSV 파일의 경로')

    def handle(self, *args, **options):
        file_path = options['file_path']  # CSV 파일 경로 가져오기

        try:
            with open(file_path, 'r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    # 데이터를 Game 모델에 저장
                    Game.objects.get_or_create(
                        appID=int(row['appID']),
                        name=row['name'],
                        supported_languages=eval(row['supported_languages']),  # 문자열 -> 리스트 변환
                        genres=eval(row['genres']),  # 문자열 -> 리스트 변환
                        header_image=row['header_image']
                    )
            self.stdout.write(self.style.SUCCESS("CSV 데이터를 성공적으로 적재했습니다."))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"파일을 찾을 수 없습니다: {file_path}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"오류 발생: {str(e)}"))
