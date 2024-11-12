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
import datetime
from urllib.parse import quote

SLACK_TOKEN = 'YOUR-SLACK-TOKEN'
SLACK_SIGNING_SECRET = 'YOUR-SIGNING-SECRET'

client = WebClient(token=SLACK_TOKEN)

# 중복 이벤트를 추적할 메모리 저장소 (예시로 메모리에 저장)
processed_events = set()

def is_valid_request(req):
    # 요청의 타임스탬프와 서명 헤더 가져오기
    timestamp = req['headers']['x-slack-request-timestamp']
    signature = req['headers']['x-slack-signature']

    # 요청이 5분 이상 오래된 경우 무효 처리
    if abs(int(time.time()) - int(timestamp)) > 605:
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

    found = False
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
            event_id = event.get('event_id', None)  # 이벤트의 고유 ID

            # 이미 처리한 이벤트라면 건너뛰기
            if event_id and event_id in processed_events:
                print(f"Event {event_id} already processed.")
                return {
                    'statusCode': 200,
                    'body': json.dumps('OK')
                }

            # 이벤트 ID를 처리된 목록에 추가
            if event_id:
                processed_events.add(event_id)

            # 봇의 ID를 가져오기
            bot_id = client.api_call("auth.test")['user_id']
            if user != bot_id:
                if text == '1' or text == '4' or text == '6':
                    if text == '1':
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

                        if text == '4':
                            today = datetime.datetime.today()
                            weekday = today.weekday()
                            count = -1
                            for img in soup.find_all('img'):
                                if img.get('data-lazy-src'):
                                    count += 1
                                    if count != weekday:
                                        continue
                                    else:
                                        img_url = img.get('data-lazy-src')
                                        found = True
                                        try:
                                            client.chat_postMessage(
                                                channel=channel,
                                                text=f"오늘 {fn}호점의 메뉴는 아래와 같습니다!",
                                                attachments=[{
                                                    "image_url": img_url,
                                                    "text": "See the image above."
                                                }]
                                            )
                                        except SlackApiError as e:
                                            print(f"Error sending message: {e.response['error']}")
                                        break

                        else:
                            # 블로그 글 내 이미지 찾기
                            for img in soup.find_all('img'):
                                if img.get('data-lazy-src'):
                                    img_url = img.get('data-lazy-src')
                                    found = True
                                    try:
                                        client.chat_postMessage(
                                            channel=channel,
                                            text=f"오늘 {fn}호점의 메뉴는 아래와 같습니다!",
                                            attachments=[{
                                                "image_url": img_url,
                                                "text": "See the image above."
                                            }]
                                        )
                                    except SlackApiError as e:
                                        print(f"Error sending message: {e.response['error']}")
                                    break

                        if not found:  # 이미지를 찾지 못했다면
                            # 특정 div 클래스 내의 p 태그 찾기
                            target_div = soup.find('div', class_='se-main-container')
                            # p 태그 중 클래스명이 se-text-paragraph se-text-paragraph-align-로 시작하는 것만 추출
                            p_tags = target_div.find_all('p', class_=lambda x: x and x.startswith(
                                'se-text-paragraph se-text-paragraph-align-'))

                            # &ZeroWidthSpace를 포함하는 span이 있는 p 태그 제외하고 텍스트 모으기
                            text_content = []
                            checkcount = 0
                            for p in p_tags:
                                # p 태그 내의 모든 span 태그 확인
                                spans = p.find_all('span')
                                # &ZeroWidthSpace 포함 여부 체크
                                contains_zero_width_space = any(
                                    '&ZeroWidthSpace;' in span.encode('unicode_escape').decode() for span in spans)

                                # &ZeroWidthSpace가 포함되지 않으면 텍스트를 수집
                                if not contains_zero_width_space:
                                    text_content.append(p.text.strip())
                                    checkcount += 1
                                if checkcount == 11:  # 11줄까지만 받음
                                    break

                            try:
                                client.chat_postMessage(
                                    channel=channel,
                                    text=f"{fn}호점의 메뉴는 다음과 같습니다. (이미지 없음)\n\n" + "\n\n".join(text_content)
                                )
                            except SlackApiError as e:
                                print(f"Error sending message: {e.response['error']}")

                    else:
                        print(f'Failed to retrieve the webpage: {response.status_code}')
                if "!AppIcon" in text:
                    try:
                        client.chat_postMessage(
                            channel=channel,
                            text="앱 아이콘 추천 받습니다... DM 주세요!"
                        )
                    except SlackApiError as e:
                        print(f"Error sending message: {e.response['error']}")

    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }
