from django.urls import path
from .views import StaffSearchView

app_name = 'staff'

urlpatterns = [
    path('search/staff/', StaffSearchView.as_view(), name='search-staff'),
]
