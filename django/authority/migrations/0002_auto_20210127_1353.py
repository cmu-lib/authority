# Generated by Django 3.1.5 on 2021-01-27 18:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('authority', '0001_initial'),
        ('entity', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='closematch',
            name='entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='close_matches', to='entity.person'),
        ),
        migrations.AddField(
            model_name='closematch',
            name='user_created',
            field=models.ForeignKey(editable=False, help_text='Created by user', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='closematchs_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='closematch',
            name='user_last_modified',
            field=models.ForeignKey(editable=False, help_text='Last modified by user', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='closematchs_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='authority',
            name='user_created',
            field=models.ForeignKey(editable=False, help_text='Created by user', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='authoritys_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='authority',
            name='user_last_modified',
            field=models.ForeignKey(editable=False, help_text='Last modified by user', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='authoritys_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='closematch',
            unique_together={('authority', 'identifier'), ('entity', 'authority')},
        ),
    ]