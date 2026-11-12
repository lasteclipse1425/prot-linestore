
from django.contrib import messages
from django.http import Http404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from rest_framework import generics, permissions

from .forms import (
    OrderCreateForm,
    ProfilePhotoForm,
    ProfileUpdateForm,
    ReviewForm,
)
from .models import Category, Order, OrderItem, Product, Review, UserProfile
from .serializers import ProductSerializer
from .auth_views import sign_in as auth_sign_in


class IsStaffOrReadOnly(permissions.BasePermission):
    """Allow public reads and restrict API changes to staff users."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or (
            request.user and request.user.is_authenticated and request.user.is_staff
        )


def base(request):
    return render(request, template_name='onlinestore/components/base.html')


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.select_related('category').filter(is_active=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    return render(
        request,
        'onlinestore/product/list.html',
        {'category': category, 'categories': categories, 'products': products},
    )


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsStaffOrReadOnly]
    queryset = Product.objects.select_related('category')
    serializer_class = ProductSerializer


class ProductRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsStaffOrReadOnly]
    queryset = Product.objects.select_related('category')
    serializer_class = ProductSerializer


def login_page(request):
    return auth_sign_in(request)


@never_cache
@login_required(login_url='onlinestore:sign-in')
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        photo_form = ProfilePhotoForm(request.POST, request.FILES, instance=profile)

        if form.is_valid() and photo_form.is_valid():
            form.save()
            photo_form.save()
            messages.success(request, 'Профиль успешно обновлён!')
            return redirect('onlinestore:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
        photo_form = ProfilePhotoForm(instance=profile)

    return render(
        request,
        'user/edit_profile.html',
        {'form': form, 'photo_form': photo_form, 'profile': profile},
    )


@require_POST
def logout_view(request):
    logout(request)
    return redirect('onlinestore:sign-in')


@never_cache
@login_required(login_url='onlinestore:sign-in')
def profile(request):
    return render(request, template_name='user/profile.html')


def product_detail(request, slug):
    """Display an active product and its reviews."""
    product = get_object_or_404(Product.objects.select_related('category'), slug=slug, is_active=True)
    reviews = product.reviews.all()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('onlinestore:login-page')

        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            return redirect('onlinestore:product_detail', slug=product.slug)
    else:
        form = ReviewForm()

    context = {'product': product, 'reviews': reviews, 'form': form}
    return render(request, template_name='onlinestore/product/detail.html', context=context)


def order_create(request, product_slug=None):
    product = get_object_or_404(Product, slug=product_slug) if product_slug else None

    """
    ??????? ?????. ??? ???????? ??????????????? ?????????? ??????
    ?? ???? ?????????? ????? (?????????? ????? GET/POST) ??? ?? ??????.
    """
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)

        if form.is_valid():
            order = form.save(commit=False)
            if product:
                order.product = product
            if request.user.is_authenticated:
                order.user = request.user
            quantity = form.cleaned_data['quantity']
            order.quantity = quantity

            if product is not None and product.is_pdf() and product.pdf_price is None:
                messages.error(request, '???? PDF-?????? ?? ???????.')
                return redirect('onlinestore:product_detail', slug=product.slug)

            order.save()

            if product is not None:
                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=product.pdf_price if product.is_pdf() else product.price,
                    quantity=quantity,
                )
                order.total_price = order_item.get_cost()
                order.save()

            request.session['last_order_id'] = order.id
            return redirect('onlinestore:order_created', order_id=order.id)
    else:
        form = OrderCreateForm(initial={'quantity': 1})

    context = {'form': form, 'product': product}
    return render(request, template_name='onlinestore/order/create.html', context=context)


def order_created(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.user_id:
        if not request.user.is_authenticated or order.user_id != request.user.id:
            raise Http404
    elif request.session.get('last_order_id') != order.id:
        return get_object_or_404(Order, pk=None)
    return render(request, template_name='onlinestore/order/created.html', context={'order': order})
