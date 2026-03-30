from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='profile_photo',
            field=models.ImageField(
                blank=True, null=True,
                upload_to='profile_photos/',
                help_text='Profile photo shown in topbar and profile dropdown.'
            ),
        ),
    ]
