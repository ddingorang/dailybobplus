from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
from bs4 import BeautifulSoup
import os
import re
import hmac
import hashlib
import time
import json

SLACK_TOKEN = 'your-slack-token'
SLACK_SIGNING_SECRET = 'your-signing-secret'

client = WebClient(token=SLACK_TOKEN)


# 파일 이름에서 유효하지 않은 문자를 제거하는 함수
# def sanitize_filename(filename):
#     return re.sub(r'[<>:"/\\|*]', '_', filename)


def is_valid_request(req):
    # 요청의 타임스탬프와 서명 헤더 가져오기
    timestamp = req['headers']['x-slack-request-timestamp']
    signature = req['headers']['x-slack-signature']

    # 요청이 5분 이상 오래된 경우 무효 처리
    if abs(int(time.time()) - int(timestamp)) > 5:
        return False

    # 서명 문자열 생성
    sig_basestring = f"v0:{timestamp}:{req['body']}"
    my_signature = 'v0=' + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()

    # 서명 비교
    return hmac.compare_digest(my_signature, signature)


def slack_events(event, context):
    if not is_valid_request(event):
        return "Unauthorized", 403
    data = json.loads(event['body'])

    # 슬랙의 이벤트를 확인
    if 'challenge' in data:
        return {
            'statusCode': 200,
            'body': json.dumps({'challenge': data['challenge']})
        }

    if 'event' in data:
        event = data['event']
        print(event)
        # 메시지가 봇의 것인지 확인
        if event.get('type') == 'message' and 'subtype' not in event:
            user = event['user']
            channel = event['channel']
            text = event['text']

            # 봇의 ID를 가져오기
            bot_id = client.api_call("auth.test")['user_id']
            if user != bot_id:
                if text == '1' or text == '4' or text == '6':
                    if text == '1':
                        # 웹 페이지 가져오기
                        url = 'https://blog.naver.com/PostList.naver?blogId=babplus123&from=postList&categoryNo=20'
                        fn = '1'
                    elif text == '4':
                        url = 'https://blog.naver.com/PostList.naver?blogId=babplus123&from=postList&categoryNo=18'
                        fn = '4'
                    elif text == '6':
                        url = 'https://blog.naver.com/PostList.naver?blogId=babplus123&from=postList&categoryNo=19'
                        fn = '6'
                    response = requests.get(url)
                    # 응답이 성공적인지 확인
                    if response.status_code == 200:
                        # Beautiful Soup 객체 생성
                        soup = BeautifulSoup(response.content, 'html.parser')
                        # print(soup)
                        # os.makedirs("images", exist_ok=True)
                        for img in soup.find_all('img'):
                            if img.get('data-lazy-src'):
                                img_url = img.get('data-lazy-src')
                                # print(img_url)
                                # # 이미지 다운로드
                                # try:
                                #     img_data = requests.get(img_url).content
                                #     #img_name = os.path.join('images', sanitize_filename(img_url.split('/')[-1]).split('?')[0])  # 파일 이름 생성
                                #     img_name = os.path.join('images', f'{fn}.jpg')
                                #     with open(img_name, 'wb') as f:
                                #         f.write(img_data)
                                #     print(f'Downloaded: {img_name}')
                                # except Exception as e:
                                #     print(f'Could not download {img_url}: {e}')

                                try:
                                    client.chat_postMessage(
                                        channel=channel,
                                        text=f"오늘 {fn}호점의 메뉴는 아래와 같습니다",
                                        attachments=[{
                                            "image_url": img_url,
                                            "text": "See the image above."
                                        }]
                                    )
                                except SlackApiError as e:
                                    print(f"Error sending message: {e.response['error']}")
                                break
                    else:
                        print(f'Failed to retrieve the webpage: {response.status_code}')
                # else :
                #     # 사용자 메시지에 응답
                #     response_text = f"1, 4, 6 중 하나를 입력해 주세요."
                #     try:
                #         client.chat_postMessage(channel=channel, text=response_text)
                #     except SlackApiError as e:
                #         print(f"Error sending message: {e.response['error']}")
    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }

