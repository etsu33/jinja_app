from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0005_userprofile_current_period_end_and_more")]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="birthday",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="birth_time",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="birth_place",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="worship_style",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
