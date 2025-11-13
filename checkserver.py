import requests 
from bs4 import BeautifulSoup
import json
import os

#webhook = '' #Discord webhook 주소
webhook = os.environ.get('DISCORD_WEBHOOK') #Github Actions를 위한 변수, 로컬에서 사용시 이 라인은 지울것
mmhome = 'https://mabinogimobile.nexon.com/News/notice/GetList'
BASE_DETAIL_URL = "https://mabinogimobile.nexon.com/News/Notice/"
savefile = r'alert_log.txt'
ids = ''

with open(savefile, 'r', encoding='utf-8') as f:
    ids = f.read().strip()

def saveids():
    global ids
    with open(savefile, 'w', encoding='utf-8') as f:
        f.write(ids)

def getdata():
    global ids
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'X-Timezone': 'Asia/Seoul',
            'content-type': 'multipart/form-data; boundary=----WebKitFormBoundarylwJbu0U0BHhimMan'
        }
        data = '------WebKitFormBoundarylwJbu0U0BHhimMan\nContent-Disposition: form-data; name="headlineId"\n\n\n------WebKitFormBoundarylwJbu0U0BHhimMan\nContent-Disposition: form-data; name="directionType"\n\nDEFAULT\n------WebKitFormBoundarylwJbu0U0BHhimMan\nContent-Disposition: form-data; name="pageno"\n\n1\n------WebKitFormBoundarylwJbu0U0BHhimMan--'
        response = requests.post(mmhome, headers=headers, timeout=30, data=data)
        response.raise_for_status()
        html_doc = response.text
        if response.status_code != 200:
            print(f"웹페이지를 가져오는 중 오류 발생: 상태 코드 {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"웹페이지를 가져오는 중 오류 발생: {e}")
        return None

    wlist = BeautifulSoup(html_doc, 'html.parser')

    if not wlist:
        print("ERROR: 웹페이지 파싱 중 오류 발생")
        print(html_doc)
        return None

    titletags = wlist.find_all('a', class_='title')

    if titletags:
        rst = []
        for i, tag in enumerate(titletags, 1):
            
            title = tag.get_text(strip=True)

            #점검 공지만 필터
            if title.find("점검") == -1:
                continue

            #최근에 올라온 공지만 필터
            if tag['class'] != 'title new':
                continue
            
            thread_id = tag.attrs['onclick']
            if thread_id.find('Thread.link(') != -1:
                thread_id = thread_id.split('Thread.link(')[1].split(',')[0]
            else:
                continue

            turl = ""
            if thread_id:
                turl = f"{BASE_DETAIL_URL}{thread_id}"

            print(f"--- {i} ---")
            print(f"제목: {title}")
            print(f"링크: {turl}")
            rst.append({'title': title, 'url': turl})

            ids += f"{thread_id}\n"
        print("--------------------------------------------------")
        return rst
    else:
        print("페이지에서 제목 태그를 찾을 수 없습니다.")


def sendwebhook(datas):
    if datas is None or len(datas) == 0:
        return
    
    embeds = []
    for item in datas[:5]:
        embeds.append({
            "title": item['title'],
            "url": item['url'],
            "color": 3447003,
        })

    payload = {
        "username": "Test",
        "content": f"📢 **점검 공지를 감지했습니다.** 자세한 내용은 아래를 확인하세요.",
        "embeds": embeds
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(webhook, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        print("Discord 웹훅 전송됨")
        saveids()
    except requests.exceptions.RequestException as e:
        print(f"Discord 웹훅 전송 실패: {e}")
        print(f"응답 상태 코드: {response.status_code if 'response' in locals() else 'N/A'}")

sendwebhook(getdata())
