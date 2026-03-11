# Generated migration for updated Cart model and new CartItem model

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0006_cart"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Remove old ManyToManyField (drops books_cart_books table)
        migrations.RemoveField(
            model_name="cart",
            name="books",
        ),
        # Change user from ForeignKey to OneToOneField
        migrations.AlterField(
            model_name="cart",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cart",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Add created_at
        migrations.AddField(
            model_name="cart",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        # Add updated_at
        migrations.AddField(
            model_name="cart",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        # Create CartItem model
        migrations.CreateModel(
            name="CartItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("quantity", models.PositiveIntegerField(default=1)),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="books.book",
                    ),
                ),
                (
                    "cart",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="books.cart",
                    ),
                ),
            ],
        ),
        # Add unique constraint for (cart, book)
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.UniqueConstraint(
                fields=["cart", "book"], name="unique_cart_book"
            ),
        ),
    ]
