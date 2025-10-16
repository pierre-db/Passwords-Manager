from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('check_login/', views.check_login, name='check_login'),
    path('fetch_data/', views.fetch_data, name='fetch_data'),
    path('logout/', views.logout_view, name='logout'),
]