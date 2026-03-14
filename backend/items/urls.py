from django.urls import path
from .views import (
    ItemListCreateView, ItemDetailView,
    ResolveItemView, HandoverUpdateView, StatusChangeView,
    MyItemsView, MatchListView, MatchReviewView,
    AdminAnalyticsView, DashboardView,
)

urlpatterns = [
    path('items/',                  ItemListCreateView.as_view(),  name='item_list_create'),
    path('items/mine/',             MyItemsView.as_view(),         name='item_mine'),
    path('items/<int:pk>/',         ItemDetailView.as_view(),      name='item_detail'),
    path('items/<int:pk>/resolve/', ResolveItemView.as_view(),     name='item_resolve'),
    path('items/<int:pk>/handover/', HandoverUpdateView.as_view(), name='item_handover'),
    path('items/<int:pk>/status/',  StatusChangeView.as_view(),    name='item_status'),

    path('matches/',                MatchListView.as_view(),        name='match_list'),
    path('matches/<int:pk>/review/', MatchReviewView.as_view(),    name='match_review'),

    path('analytics/',              AdminAnalyticsView.as_view(),  name='analytics'),
    path('dashboard/',              DashboardView.as_view(),       name='dashboard'),
]
