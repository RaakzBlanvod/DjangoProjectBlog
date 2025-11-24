from django.urls import path
from .views import about, rules, StaticPageView, csrf_failure, page_not_found, server_error

app_name = 'pages'

urlpatterns = [
    path('about/', about, name='about'),
    path('rules/', rules, name='rules'),

    path('cbv/about/', StaticPageView.as_view(), name='about_cbv'),
    path('cbv/rules/', StaticPageView.as_view(), name='rules_cbv'),
    
    path('cbv/<str:page>/', StaticPageView.as_view(), name='static_page'),

    path('test/403/', csrf_failure),
    path('test/404/', page_not_found),
    path('test/500/', server_error),
]