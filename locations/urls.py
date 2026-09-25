from django.urls import path
from . import views

app_name = 'locations'

urlpatterns = [
    path('food/map/', views.map_view, name='map_view'),
    path('api/locations/search/', views.location_search_api, name='search_api'),
]
