from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0002_company_next_invoice_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='business_category',
            field=models.CharField(
                blank=True,
                choices=[
                    ('restaurant', '🍕 Restaurant / Café'),
                    ('grocery', '🛒 Grocery / Supermarket'),
                    ('pharmacy', '💊 Pharmacy'),
                    ('salon', '💇 Salon / Spa'),
                    ('retail', '👗 Retail / Fashion'),
                    ('flower', '🌸 Flower / Gift Shop'),
                    ('cloud_kitchen', '☁️ Cloud Kitchen'),
                    ('bakery', '🥖 Bakery'),
                    ('electronics', '📱 Electronics'),
                    ('general', '🏪 General / Other'),
                ],
                default='general',
                max_length=50,
            ),
        ),
    ]
