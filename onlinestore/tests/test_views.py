import pytest

from onlinestore.models import Product, Category


@pytest.mark.django_db
def test_product_list_view(client):
    category = Category.objects.create(
        name="Book",
        slug="book"
    )

    Product.objects.create(
        category=category,
        name="Book 1",
        slug="book-1",
        price=1000,
        stock=5
    )

    response = client.get("/api/products/")

    assert response.status_code == 200