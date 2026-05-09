from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("temples", "0082_force_recreate_featureusage_table"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductionDataBootstrapRun",
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
                ("step", models.CharField(max_length=100)),
                ("version", models.CharField(max_length=100)),
                ("command", models.CharField(max_length=100)),
                ("args", models.JSONField(blank=True, default=list)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("running", "Running"),
                            ("success", "Success"),
                            ("failed", "Failed"),
                        ],
                        default="running",
                        max_length=16,
                    ),
                ),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("last_error", models.TextField(blank=True, default="")),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name="productiondatabootstraprun",
            constraint=models.UniqueConstraint(
                fields=("step", "version"),
                name="uniq_production_bootstrap_step_version",
            ),
        ),
        migrations.AddIndex(
            model_name="productiondatabootstraprun",
            index=models.Index(
                fields=["status", "updated_at"],
                name="idx_bootstrap_status_updated",
            ),
        ),
        migrations.AddIndex(
            model_name="productiondatabootstraprun",
            index=models.Index(
                fields=["step", "version"],
                name="idx_bootstrap_step_version",
            ),
        ),
    ]
