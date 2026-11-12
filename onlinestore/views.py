
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Case, DecimalField, F, Q, When
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _, ngettext
from rest_framework import generics
from rest_framework.permissions import IsAdminUser, SAFE_METHODS

from .forms import (
    OrderCreateForm,
    ProfilePhotoForm,
    ProfileUpdateForm,
    ReviewForm,
)
from .models import Category, Order, OrderItem, Product, Review, UserProfile
from .serializers import ProductSerializer
from .auth_views import sign_in as auth_sign_in


def base(request):
    return redirect('main:product_list')


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.select_related('category').filter(is_active=True)
    query = request.GET.get('q', '').strip()[:100]
    sort = request.GET.get('sort', 'newest')

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(author__icontains=query)
            | Q(description__icontains=query)
        )

    selling_price = Case(
        When(file__iendswith='.pdf', pdf_price__isnull=False, then=F('pdf_price')),
        default=F('price'),
        output_field=DecimalField(max_digits=10, decimal_places=2),
    )
    if sort == 'price_asc':
        products = products.order_by(selling_price, '-created_at')
    elif sort == 'price_desc':
        products = products.order_by(selling_price.desc(), '-created_at')
    else:
        sort = 'newest'
        products = products.order_by('-created_at')

    page_obj = Paginator(products, 12).get_page(request.GET.get('page'))
    return render(
        request,
        'onlinestore/product/list.html',
        {
            'category': category,
            'categories': categories,
            'products': page_obj.object_list,
            'page_obj': page_obj,
            'query': query,
            'sort': sort,
        },
    )


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]


class ProductListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        products = Product.objects.select_related('category')
        if not self.request.user.is_staff:
            products = products.filter(is_active=True)
        return products

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return []
        return super().get_permissions()


class ProductRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        products = Product.objects.select_related('category')
        if not self.request.user.is_staff:
            products = products.filter(is_active=True)
        return products

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return []
        return super().get_permissions()


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
            messages.success(request, _('Your profile has been updated.'))
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
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    orders = request.user.orders.prefetch_related('items__product')
    return render(
        request,
        template_name='user/profile.html',
        context={'profile': profile, 'orders': orders},
    )


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related('category'), slug=slug, is_active=True)
    reviews = product.reviews.select_related('user').all()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('onlinestore:login-page')

        form = ReviewForm(request.POST)
        if form.is_valid():
            if Review.objects.filter(product=product, user=request.user).exists():
                form.add_error(None, _('You have already reviewed this product.'))
            else:
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
    if not product_slug:
        return redirect('onlinestore:product_list')
    product = get_object_or_404(Product, slug=product_slug, is_active=True)

    """
    ??????? ?????. ??? ???????? ??????????????? ?????????? ??????
    ?? ???? ?????????? ????? (?????????? ????? GET/POST) ??? ?? ??????.
    """
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)

        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            if product.is_pdf() and product.pdf_price is None:
                form.add_error(None, _('A price has not been set for the digital download.'))
            elif not product.is_pdf() and quantity > product.stock:
                form.add_error('quantity', _stock_error(product.stock))
            elif not product.is_pdf():
                with transaction.atomic():
                    product = Product.objects.select_for_update().get(pk=product.pk)
                    if quantity > product.stock:
                        form.add_error('quantity', _stock_error(product.stock))
                    else:
                        price = product.selling_price
                        order = form.save(commit=False)
                        order.product = product
                        order.quantity = quantity
                        order.total_price = price * quantity
                        if request.user.is_authenticated:
                            order.user = request.user
                        order.save()
                        OrderItem.objects.create(order=order, product=product, price=price, quantity=quantity)
                        product.stock -= quantity
                        product.save(update_fields=['stock', 'updated_at'])
                        request.session['guest_order_id'] = order.pk
                        return redirect('onlinestore:order_created', order_id=order.id)
            else:
                price = product.selling_price
                order = form.save(commit=False)
                order.product = product
                order.quantity = quantity
                order.total_price = price * quantity
                if request.user.is_authenticated:
                    order.user = request.user
                order.save()
                OrderItem.objects.create(order=order, product=product, price=price, quantity=quantity)
                request.session['guest_order_id'] = order.pk
                return redirect('onlinestore:order_created', order_id=order.id)
    else:
        form = OrderCreateForm(initial={'quantity': 1})

    context = {'form': form, 'product': product}
    return render(request, template_name='onlinestore/order/create.html', context=context)


def order_created(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), id=order_id)
    if request.user.is_authenticated:
        if order.user_id != request.user.id:
            raise Http404
    elif order.user_id is not None or request.session.get('guest_order_id') != order.pk:
        raise Http404
    return render(request, template_name='onlinestore/order/created.html', context={'order': order})


def _stock_error(available):
    if available == 0:
        return _('This product is currently out of stock.')
    return ngettext(
        'Only %(quantity)s unit is currently in stock.',
        'Only %(quantity)s units are currently in stock.',
        available,
    ) % {'quantity': available}


@login_required(login_url='onlinestore:sign-in')
def download_product_pdf(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    if not product.is_pdf() or not OrderItem.objects.filter(
        product=product, order__user=request.user, order__status=Order.StatusChoices.PAID
    ).exists():
        raise Http404
    return FileResponse(product.file.open('rb'), as_attachment=True, filename=product.file.name.rsplit('/', 1)[-1])
