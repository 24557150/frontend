# views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from .models import ClosetImage, MimicImage, RecommendationResult  # 你需先建立這些模型
import os
from datetime import datetime


def home(request):
    return render(request, 'home.html')

# 1️⃣ LIFF 頁面：衣櫃圖片上傳頁面
def closet_upload_view(request):
    return render(request, 'liff/closet_upload.html', {
        'liff_id': settings.LIFF_ID
    })


# 2️⃣ LIFF 頁面：模仿穿搭上傳頁面
def mimic_upload_view(request):
    return render(request, 'liff/mimic_upload.html', {
        'liff_id': settings.LIFF_ID
    })


# 3️⃣ 圖片 POST 上傳處理：衣櫃圖片
def upload_closet(request):
    if request.method == 'POST':
        user_id = request.POST.get('userId')
        category = request.POST.get('category', 'top')
        image_file = request.FILES.get('image')

        if not (user_id and image_file):
            return JsonResponse({'error': '缺少必要欄位'}, status=400)

        # 儲存圖片
        folder = os.path.join(settings.MEDIA_ROOT, 'closet')
        os.makedirs(folder, exist_ok=True)
        filename = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        path = os.path.join(folder, filename)

        with open(path, 'wb+') as f:
            for chunk in image_file.chunks():
                f.write(chunk)

        # 可改為存進模型
        # ClosetImage.objects.create(user_id=user_id, image='closet/' + filename, category=category)

        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': '僅支援 POST'}, status=405)


# 4️⃣ 圖片 POST 上傳處理：模仿穿搭圖片
def upload_mimic(request):
    if request.method == 'POST':
        user_id = request.POST.get('userId')
        image_file = request.FILES.get('image')

        if not (user_id and image_file):
            return JsonResponse({'error': '缺少必要欄位'}, status=400)

        # 儲存 mimic 圖片
        folder = os.path.join(settings.MEDIA_ROOT, 'mimic')
        os.makedirs(folder, exist_ok=True)
        filename = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        path = os.path.join(folder, filename)

        with open(path, 'wb+') as f:
            for chunk in image_file.chunks():
                f.write(chunk)

        # 可儲存到 MimicImage 資料表
        # MimicImage.objects.create(user_id=user_id, image='mimic/' + filename)

        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': '僅支援 POST'}, status=405)


# 5️⃣ 顯示 AI 穿搭推薦結果
def recommend_result_view(request):
    user_id = request.GET.get('userId')

    # 假設你已建立好推薦圖片，可以從資料庫撈出對應使用者的推薦清單
    # 以下為假資料（之後可改為 model 查詢）
    recommended_items = [
        {
            'image_url': '/media/closet/sample1.jpg',
            'description': '推薦上衣：白色襯衫'
        },
        {
            'image_url': '/media/closet/sample2.jpg',
            'description': '推薦下身：卡其長褲'
        },
        {
            'image_url': '/media/closet/sample3.jpg',
            'description': '推薦鞋子：白球鞋'
        },
    ]

    return render(request, 'liff/recommend_result.html', {
        'recommended_items': recommended_items
    })
