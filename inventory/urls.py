from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [

    # PRODUCTS
    path("", views.inventory, name="inventory"),
    path("add/", views.add_product, name="add_product"),
    path("edit/<int:id>/", views.edit_product, name="edit_product"),
    path("delete/<int:id>/", views.delete_product, name="delete_product"),

    # CATEGORIES
    path("categories/", views.category_list, name="categories"),
    path("category/add/", views.add_category, name="add_category"),
    path("category/edit/<int:id>/", views.edit_category, name="edit_category"),
    path("category/delete/<int:id>/", views.delete_category, name="delete_category"),

    # SUPPLIERS
    path("suppliers/", views.suppliers, name="suppliers"),
    path("supplier/add/", views.add_supplier, name="add_supplier"),
    path("supplier/edit/<int:id>/", views.edit_supplier, name="edit_supplier"),
    path("supplier/delete/<int:id>/", views.delete_supplier, name="delete_supplier"),

    # PURCHASES
    path("purchases/", views.purchases, name="purchases"),
    path("purchase/add/", views.add_purchase, name="add_purchase"),

    # STOCK HISTORY
    path("stock-history/", views.stock_history, name="stock_history"),
]