from django.contrib import admin
from .models import Category, Product, Order, OrderItem, UserProfile, Review

admin.site.register(UserProfile)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "stock", "is_active", "created_at"]
    list_filter = ["is_active", "category"]
    list_editable = ["price", "stock", "is_active"]
    prepopulated_fields = {"slug": ("name",)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ["product"]
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "first_name", "last_name", "email", "status", "created_at", "get_total_cost"]
    list_filter = ["status", "created_at"]
    inlines = [OrderItemInline]