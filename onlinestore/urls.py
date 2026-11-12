from django.urls import path
from . import auth_views, views
from .views import (
    ProductDetailAPIView,
    ProductListCreateAPIView,
    ProductRetrieveUpdateDestroyAPIView,
)


app_name = "onlinestore"

urlpatterns = [
    path(
        "products/",
        views.product_list,
        name="products_list"
    ),

    path(
        'base/', 
         views.base, 
         name='base'
    ),

    # path(
    #     'api/products/',
    #     ProductListAPIView.as_view(),
    #     name='product-list'
    # ),
    
    path(
        'api/products/',
        ProductListCreateAPIView.as_view(),
        name='product-list'
    ),

    path(
        'api/products/<int:pk>/',
        ProductRetrieveUpdateDestroyAPIView.as_view(),
        name='product-detail'
    ),
    
    path(
        'profile/edit/',
        views.edit_profile,
        name='edit-profile'
    ),

    path(
        'login_page/', 
         views.login_page, 
         name='login-page'
    ),
    path(
        'logout/', 
         views.logout_view, 
         name='logout'
    ),

     path(
         'sign_in/', 
           auth_views.sign_in,
          name='sign-in'
    ),
    path(
         'sign-in/',
          auth_views.sign_in,
          name='sign_in_alias'
    ),
     path(
         'profile/', 
          views.profile, 
          name='profile'
    ),
    path(
        'register/',
        auth_views.register,
        name='register'
    ),
    path(
        'api/register/',
        auth_views.register_api,
        name='register_api'
    ),

    # Главная страница магазина (список всех активных товаров)
    path("", views.product_list, name="product_list"),
    
    # Фильтрация товаров по определенной категории
    path(
        "category/<slug:category_slug>/",
        views.product_list,
        name="product_list_by_category"
    ),
    
    # Детальная страница отдельного товара
    path(
        "product/<slug:slug>/",
        views.product_detail,
        name="product_detail"
    ),
    
    # Страница и процесс создания заказа
    path(
        "order/create/",
        views.order_create,
        name="order_create"
        
    ),
    path('order/create/<slug:product_slug>/', 
         views.order_create, 
         name='order_create_product'
    ),
    
    # Страница успешного оформления заказа
    path(
        "order/created/<int:order_id>/",
        views.order_created,
        name="order_created"
    ),
]