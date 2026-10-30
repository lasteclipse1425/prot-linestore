import pytest

from onlinestore.models import Product, Category


@pytest.mark.django_db
def test_product_creation():
    category = Category.objects.create(
        name="Book",
        slug="book"
    )

    product = Product.objects.create(
        category=category,
        name="Python Book",
        slug="python-book",
        price=5000,
        stock=10
    )

    assert product.name == "Python Book"
    assert product.stock == 10