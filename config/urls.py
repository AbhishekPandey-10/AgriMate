from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core import views # Import your views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth System (Built-in)
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # App Logic
    path('', views.dashboard, name='dashboard'),
    path('add-crop/', views.crop_add, name='add_crop'),
    path('add-expense/', views.expense_add, name='add_expense'),
    path('harvest/<int:cycle_id>/', views.crop_harvest, name='harvest_crop'),
    path('generate-report/', views.generate_pdf, name='generate_pdf'),
    path('switch-language/', views.switch_language, name='switch_language'),
    
    # API Endpoints (AJAX)
    path('api/mandi-prices/', views.api_mandi_prices, name='api_mandi_prices'),
    path('api/crop-forecast/', views.api_crop_forecast, name='api_crop_forecast'),
    
    path('', include('pwa.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
