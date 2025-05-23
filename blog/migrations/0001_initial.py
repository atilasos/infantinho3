# Generated by Django 5.2 on 2025-04-29 13:23

# import ckeditor.fields
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('conteudo', models.TextField(verbose_name='content')),
                ('publicado_em', models.DateTimeField(default=django.utils.timezone.now, verbose_name='published at')),
                ('removido', models.BooleanField(default=False, help_text='Indicates if the comment has been removed by moderation.', verbose_name='removed')),
                ('removido_em', models.DateTimeField(blank=True, help_text='Timestamp when the comment was removed.', null=True, verbose_name='removed at')),
                ('motivo_remocao', models.CharField(blank=True, help_text='Reason provided for removing the comment.', max_length=255, verbose_name='reason for removal')),
            ],
            options={
                'verbose_name': 'Comment',
                'verbose_name_plural': 'Comments',
                'ordering': ['publicado_em'],
            },
        ),
        migrations.CreateModel(
            name='ModerationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acao', models.CharField(choices=[('REMOVER_POST', 'Remove Post'), ('RESTAURAR_POST', 'Restore Post'), ('REMOVER_COMMENT', 'Remove Comment')], help_text='The type of moderation action performed.', max_length=20, verbose_name='action')),
                ('data', models.DateTimeField(default=django.utils.timezone.now, verbose_name='timestamp')),
                ('motivo', models.CharField(blank=True, help_text='Optional reason provided by the moderator.', max_length=255, verbose_name='reason')),
                ('conteudo_snapshot', models.TextField(blank=True, help_text='A snapshot of the content at the time of the action.', verbose_name='content snapshot')),
            ],
            options={
                'verbose_name': 'Moderation Log Entry',
                'verbose_name_plural': 'Moderation Log Entries',
                'ordering': ['-data'],
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(blank=True, help_text='Optional title for the post.', max_length=200, verbose_name='title')),
                ('conteudo', models.TextField(verbose_name='content')),
                ('image', models.ImageField(blank=True, help_text='Optional image associated with the post.', null=True, upload_to='blog_images/%Y/%m/', verbose_name='image')),
                ('attachment', models.FileField(blank=True, help_text='Optional file attachment (e.g., PDF).', null=True, upload_to='blog_attachments/%Y/%m/', verbose_name='attachment')),
                ('publicado_em', models.DateTimeField(default=django.utils.timezone.now, verbose_name='published at')),
                ('status', models.CharField(choices=[('PENDING', 'Pending Approval'), ('PUBLISHED', 'Published')], default='PENDING', help_text='Publication status of the post.', max_length=10, verbose_name='status')),
                ('approved_at', models.DateTimeField(blank=True, help_text='Timestamp when the post was approved.', null=True, verbose_name='approved at')),
                ('categoria', models.CharField(choices=[('AVISO', 'Announcement'), ('PROJETO', 'Project Update'), ('TRABALHO', 'Student Work'), ('OUTRO', 'Other')], default='OUTRO', help_text='The main category of the post.', max_length=20, verbose_name='category')),
                ('removido', models.BooleanField(default=False, help_text='Indicates if the post has been removed by moderation.', verbose_name='removed')),
                ('removido_em', models.DateTimeField(blank=True, help_text='Timestamp when the post was removed.', null=True, verbose_name='removed at')),
                ('motivo_remocao', models.CharField(blank=True, help_text='Reason provided for removing the post.', max_length=255, verbose_name='reason for removal')),
            ],
            options={
                'verbose_name': 'Post',
                'verbose_name_plural': 'Posts',
                'ordering': ['-publicado_em'],
            },
        ),
    ]
