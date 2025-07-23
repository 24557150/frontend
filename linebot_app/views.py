from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import os
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .models import ClosetItem
from django.http import JsonResponse
from django.core.files.storage import default_storage
from pathlib import Path
 


# 將以下設定寫入 settings.py 中
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "cMmRHEkKdOaJWv9LdQk1RIedv5DX3qKpg8O7SIXqiIi3yp0jcdXy6xJtlM7eBqV0HigKhWoWkKb85hArSFwalPguOoig6KwqCI7dYasf/hUxOEMVugV/snhSltG1msJ6bcE1kl61lSOqE1/wiV8XOQdB04t89/1O/w1cDnyilFU=")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "93ec1dfd2a32b6c2819eda90cc28d485")

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)

@csrf_exempt
def callback(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request")

    signature = request.headers.get('X-Line-Signature')
    body = request.body.decode('utf-8')

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return HttpResponseBadRequest("Invalid signature")

    return HttpResponse("OK")

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text

    if user_msg == "衣櫃":
        reply = "點擊進入衣櫃： https://你的LIFF網址/liff/closet/"
    elif user_msg == "穿搭":
        reply = "模仿穿搭： https://你的LIFF網址/liff/mimic/"
    elif user_msg == "推薦":
        reply = "推薦結果： https://你的LIFF網址/liff/recommend/"
    else:
        reply = "請點選選單或輸入：衣櫃 / 穿搭 / 推薦"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )
    
    
@csrf_exempt
def upload_closet(request):
    if request.method == 'POST':
        user_id = request.POST.get('userId')
        category = request.POST.get('category')
        files = request.FILES.getlist('images')
        

        saved = []
        
        # 重要：檢查必填欄位
        if not user_id or not category or not files:
            return JsonResponse({'status': 'error', 'message': '缺少參數'}, status=400)
        
        for f in files:
            item = ClosetItem(user_id=user_id, category=category, image=f)
            item.save()
            
            saved.append({
                'url': item.image.url,
                'category': item.category
            })

        return JsonResponse({'status': 'success', 'images': saved})

    return JsonResponse({'error': 'Invalid request'}, status=400)
    

# def view_closet(request, user_id):
#     images = ClosetItem.objects.filter(user_id=user_id)

#     image_list = []
#     for image in images:
#         image_list.append({
#             "url": f"{settings.MEDIA_URL}{image.image.name}",
#             "category": image.category
#         })

#     return JsonResponse({"images": image_list})

# def view_closet(request, user_id):
#     folder_path = Path(f'{settings.MEDIA_ROOT}/{user_id}')
#     files = [f for f in folder_path if f.is_file()]
    
#     urls = []
#     for f in files:
#         url = {
#                 'url': f,
#                 'category': ""
#             }
#         urls.append(url)
    
#     return JsonResponse({'images': urls})


# def view_closet(request, user_id):
#     url = request.path
    
#     user_id = url.rstrip('/').split('/')[-1]
#     # user_id = request.POST.get('userId')
#     # category = request.POST.get('category')
#     files = request.FILES.getlist('images')
    
#     folder_path = Path(f'{settings.MEDIA_ROOT_CLOSET}/{user_id}')
#     files = [
#         f'{settings.MEDIA_CLOSET_PARTIAL_PATH}/{user_id}/{f}' for f in os.listdir(folder_path)
#         if os.path.isfile(os.path.join(folder_path, f))
#     ]
#     # items = ClosetItem(user_id=user_id, category=category, image=f)
 
#     return JsonResponse({'images': files})

# def view_closet(request, user_id):
#     base_path = Path(f'{settings.MEDIA_ROOT}/closet/{user_id}')
#     images = []

#     if base_path.exists():
#         for category_dir in base_path.iterdir():
#             if category_dir.is_dir():
#                 category = category_dir.name
#                 for f in category_dir.iterdir():
#                     if f.is_file():
#                         images.append({
#                             'url': f"{settings.MEDIA_URL}closet/{user_id}/{category}/{f.name}",
#                             'category': category
#                         })

#     return JsonResponse({'images': images})
# def view_closet(request, user_id):
#     base_path = os.path.join(settings.MEDIA_ROOT, 'closet', user_id)
#     if not os.path.exists(base_path):
#         return JsonResponse({'images': []})

#     result = []
#     for category in os.listdir(base_path):
#         category_path = os.path.join(base_path, category)
#         if os.path.isdir(category_path):
#             for filename in os.listdir(category_path):
#                 image_url = f"/media/closet/{user_id}/{category}/{filename}"
#                 result.append({'category': category, 'url': image_url})

#     return JsonResponse({'images': result})




def view_closet(request, user_id):
    media_root = '/home/babomomo26/AIOutfit/media/closet'  # ✅ 實體儲存目錄根路徑
    base_url = 'media/closet'  # ✅ 網頁可訪問的URL前綴

    user_path = os.path.join(media_root, user_id)
    image_data = []

    if os.path.exists(user_path):
        for category in os.listdir(user_path):
            category_path = os.path.join(user_path, category)
            if os.path.isdir(category_path):
                for filename in os.listdir(category_path):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        image_url = f"{base_url}/{user_id}/{category}/{filename}"
                        image_data.append({
                            "url": image_url,
                            "category": category
                        })

    return JsonResponse({"images": image_data})
