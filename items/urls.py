from django.urls import path
from . import views

urlpatterns = [
    path('', views.item_feed, name='item_feed'),
    path('report/', views.report_item, name='report_item'),
    path('<int:pk>/', views.item_detail, name='item_detail'),
    path('<int:pk>/edit/', views.edit_item, name='edit_item'),
    path('<int:pk>/delete/', views.delete_item, name='delete_item'),
]
