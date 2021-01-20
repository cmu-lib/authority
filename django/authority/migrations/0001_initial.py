# Generated by Django 3.1.5 on 2021-01-20 22:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('entity', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Authority',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Unique short readable label', max_length=4000, unique=True)),
                ('description', models.TextField(blank=True, help_text='Descriptive notes')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='Date created (automatically recorded)')),
                ('last_updated', models.DateTimeField(auto_now=True, db_index=True, help_text='Date last modified (automatically recorded)')),
                ('namespace', models.URLField(unique=True)),
                ('user_created', models.ForeignKey(editable=False, help_text='Created by user', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='authoritys_created', to=settings.AUTH_USER_MODEL)),
                ('user_last_modified', models.ForeignKey(editable=False, help_text='Last modified by user', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='authoritys_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'authorities',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CloseMatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='Date created (automatically recorded)')),
                ('last_updated', models.DateTimeField(auto_now=True, db_index=True, help_text='Date last modified (automatically recorded)')),
                ('identifier', models.CharField(max_length=1000)),
                ('authority', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='close_matches', to='authority.authority')),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='close_matches', to='entity.person')),
                ('user_created', models.ForeignKey(editable=False, help_text='Created by user', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='closematchs_created', to=settings.AUTH_USER_MODEL)),
                ('user_last_modified', models.ForeignKey(editable=False, help_text='Last modified by user', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='closematchs_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'close matches',
                'unique_together': {('entity', 'authority'), ('authority', 'identifier')},
            },
        ),
    ]
