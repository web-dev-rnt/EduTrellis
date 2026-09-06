from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0045_seed_vidhyora_ai_plans'),
    ]

    operations = [
        migrations.AddField(
            model_name='pwasettings',
            name='favicon',
            field=models.FileField(blank=True, help_text='Browser-tab icon. Upload an ICO, PNG, SVG or WebP file.', null=True, upload_to='customize/'),
        ),
        migrations.AddField(
            model_name='pwasettings',
            name='share_description',
            field=models.CharField(blank=True, default='', help_text='Short description shown beneath the heading in shared-link previews.', max_length=300),
        ),
        migrations.AddField(
            model_name='pwasettings',
            name='share_image',
            field=models.ImageField(blank=True, help_text='Link-preview image. Recommended size: 1200×630px.', null=True, upload_to='customize/'),
        ),
        migrations.AddField(
            model_name='pwasettings',
            name='share_title',
            field=models.CharField(blank=True, default='', help_text='Heading shown when a website link is shared on WhatsApp, Facebook, X and other apps.', max_length=200),
        ),
    ]
