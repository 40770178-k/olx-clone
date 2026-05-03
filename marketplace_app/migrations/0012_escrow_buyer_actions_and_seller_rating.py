from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace_app", "0011_alter_message_options_remove_item_user_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="complaint",
            name="details",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="complaint",
            name="escrow",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="complaints",
                to="marketplace_app.escrow",
            ),
        ),
        migrations.AddField(
            model_name="complaint",
            name="proof_image",
            field=models.ImageField(blank=True, null=True, upload_to="complaint_images/"),
        ),
        migrations.CreateModel(
            name="DeliveryConfirmationImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="delivery_confirmations/")),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "buyer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="delivery_confirmation_images",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "escrow",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="confirmation_images",
                        to="marketplace_app.escrow",
                    ),
                ),
            ],
            options={"ordering": ["-uploaded_at"]},
        ),
        migrations.CreateModel(
            name="SellerRating",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("stars", models.PositiveSmallIntegerField()),
                ("review", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "buyer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="submitted_ratings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "escrow",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="seller_rating",
                        to="marketplace_app.escrow",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="seller_ratings",
                        to="marketplace_app.item",
                    ),
                ),
                (
                    "seller",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="received_ratings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="sellerrating",
            constraint=models.CheckConstraint(
                condition=models.Q(stars__gte=1) & models.Q(stars__lte=5),
                name="seller_rating_stars_between_1_and_5",
            ),
        ),
    ]
