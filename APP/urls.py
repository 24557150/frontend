from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from linebot_app.views import callback

urlpatterns = [
    path('', include('outfit.urls')),         # 原 outfit 功能
    path('line/', callback),                  # 原 line callback
    path('linebot/', include('linebot_app.urls')),  # 新增：讓 linebot_app 的 URL 生效
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
