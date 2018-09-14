from django.urls import path, include
from django.conf import settings
from django.views.static import serve
import os
from . import routes

urlpatterns = [
    path('fetch/<int:resId>', routes.fetch),
    path('search/<kws>/<int:page>', routes.search),
    path('', serve, { 'path': 'index.html', 'document_root': os.path.join(settings.BASE_DIR, "web", "static") }),
]
