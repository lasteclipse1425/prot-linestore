from itertools import product
from urllib import request
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, Order, OrderItem, Review, UserProfile
from .forms import OrderCreateForm, ReviewForm, RegisterForm, ProfileUpdateForm, ProfilePhotoForm
from django.contrib.auth import login, authenticate, logout 
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from rest_framework import generics
from .serializers import ProductSerializer
from django.views.decorators.http import require_POST
# from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .forms import ProfileUpdateForm

def base(request):
    return render(request, template_name='onlinestore/components/base.html')

# class ProductListAPIView(APIView):

#     def get(self, request):
#         products = Product.objects.all()
#         serializer = ProductSerializer(products, many=True)
#         return Response(serializer.data)

#     def post(self, request):
#         serializer = ProductSerializer(data=request.data)

#         if serializer.is_valid():
#             serializer.save()
#             return Response(
#                 serializer.data,
#                 status=status.HTTP_201_CREATED
#             )

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST
#         )
    
# class ProductDetailAPIView(APIView):

#     def get_object(self, pk):
#         try:
#             return Product.objects.get(pk=pk)
#         except Product.DoesNotExist:
#             return None

#     def get(self, request, pk):
#         product = self.get_object(pk)

#         if not product:
#             return Response(
#                 {"error": "Товар не найден"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = ProductSerializer(product)
#         return Response(serializer.data)

#     def put(self, request, pk):
#         product = self.get_object(pk)

#         if not product:
#             return Response(
#                 {"error": "Товар не найден"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = ProductSerializer(
#             product,
#             data=request.data
#         )

#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     def delete(self, request, pk):
#         product = self.get_object(pk)

#         if not product:
#             return Response(
#                 {"error": "Товар не найден"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         product.delete()

#         return Response(
#             {"message": "Товар удален"},
#             status=status.HTTP_204_NO_CONTENT
#         )



def product_list(request):
    products = Product.objects.select_related(
        "category"
    ).filter(
        is_active=True
    )

    return render(
        request,
        "onlinestore/product/list.html",
        {"products": products}
    )
class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductListCreateAPIView(
    generics.ListCreateAPIView
):
    queryset = Product.objects.select_related(
        'category'
    )
    serializer_class = ProductSerializer

class ProductRetrieveUpdateDestroyAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = Product.objects.select_related(
        'category'
    )
    serializer_class = ProductSerializer

def login_page(request):
    return render(request, template_name='user/login.html')

@never_cache
@login_required(login_url='onlinestore:sign-in')
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':
        form = ProfileUpdateForm(
            request.POST,
            instance=request.user
        )
        photo_form = ProfilePhotoForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid() and photo_form.is_valid():
            form.save()
            photo_form.save()

            messages.success(
                request,
                'Профиль успешно обновлён!'
            )
            return redirect('onlinestore:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
        photo_form = ProfilePhotoForm(instance=profile)

    return render(
        request,
        'user/edit_profile.html',
        {
            'form': form,
            'photo_form': photo_form,
            'profile': profile,
        }
    )


@require_POST
def logout_view(request):
    logout(request)
    return redirect('onlinestore:sign-in')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            # автоматически авторизуем после регистрации
            login(request, user)

            messages.success(
                request,
                f'Аккаунт {user.username} успешно создан!'
            )

            return redirect('onlinestore:profile')
    else:
        form = RegisterForm()

    return render(
        request,
        template_name='user/register.html',
        context={'form': form}
    )


def sign_in(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('onlinestore:profile')

        messages.error(request, 'Wrong credentials.')

    return render(request, template_name='user/login.html')

@never_cache
@login_required(login_url='onlinestore:sign-in')
# @login_required(login_url='onlinestore:login-page')  # Перенаправление на страницу входа, если пользователь не авторизован
def profile(request):
    return render(request, template_name='user/profile.html')

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()

    products = Product.objects.select_related(
        'category'
    ).filter(
        is_active=True
    )

    if category_slug:
        category = get_object_or_404(
            Category,
            slug=category_slug
        )
        products = products.filter(
            category=category
        )

    return render(
        request,
        "onlinestore/product/list.html",
        {
            "category": category,
            "categories": categories,
            "products": products,
        }
    )
def product_detail(request, slug):
    """
    Отображает детальную страницу выбранного товара.
    """
    product = get_object_or_404(
        Product.objects.select_related('category'),
        slug=slug,
        is_active=True
    )
    reviews = product.reviews.all()
    if request.method == 'POST':
        # Проверяем, авторизован ли пользователь перед отправкой
        if not request.user.is_authenticated:
            return redirect('onlinestore:login-page')

        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            reviews = product.reviews.select_related(
                'user'
            )
            review.save()
            return redirect('onlinestore:product_detail', slug=product.slug)
    else:
        form = ReviewForm()

    context = {
        'product': product,
        'reviews': reviews,
        'form': form,
    }
    return render(request, template_name="onlinestore/product/detail.html", context=context)


def order_create(request, product_slug=None):
    product = get_object_or_404(
        Product,
        slug=product_slug
    )
    
    """
    Создает заказ. Для простоты демонстрируется оформление заказа 
    на один конкретный товар (переданный через GET/POST) или из сессии.
    """
    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        
        if form.is_valid():
            name = form.cleaned_data.get("first_name")
            order = form.save(commit=False)
            if product:
                order.product = product
            order.save()
            
            # Привязываем текущего пользователя, если он авторизован
            if request.user.is_authenticated:
                order.user = request.user
            order.save()

            # Получаем id товара и количество из формы (например, покупка в 1 клик)
            quantity = int(request.POST.get("quantity", 1))
            if product:
                order.product = product
            order.save()

            if product.is_pdf() and product.pdf_price is None:
                messages.error(request, "Цена PDF-версии не указана.")
                return redirect("onlinestore:product_detail", slug=product.slug)
                        
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                price=product.pdf_price if product.is_pdf() else product.price,
                quantity=quantity
            )

            order.quantity = quantity
            order.total_price = order_item.get_cost()
            order.save()
            # Перенаправляем на страницу успешного оформления
            return redirect(
                "onlinestore:order_created",
                order_id=order.id

             )
    else:
        #return redirect("onlinestore:product_list")
        form = OrderCreateForm(initial={'quantity': 1})

    context = {
        "form": form,
        'product': product,
    }
    return render(request, template_name="onlinestore/order/create.html", context=context)


def order_created(request, order_id):
    """
    Отображает подтверждение успешного создания заказа.
    """
    order = get_object_or_404(
        Order.objects.select_related(
            'user',
            'product'
        ),
        id=order_id
    )
    return render(request, template_name="onlinestore/order/created.html", context={"order": order})

def logout_view(request):
    logout(request)
    return redirect('onlinestore:sign-in')
