from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'id', 'category', 'image', 'name', 'author', 'slug', 'description',
            'price', 'pdf_price', 'stock', 'is_active', 'created_at', 'updated_at',
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at'
        )
