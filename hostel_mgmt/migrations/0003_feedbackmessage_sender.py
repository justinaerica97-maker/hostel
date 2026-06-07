from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hostel_mgmt', '0002_remove_customuser_email_verification_token_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedbackmessage',
            name='sender',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='sent_feedback',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
