from django.db import migrations


def seed_program_settings(apps, schema_editor):
    ProgramSettings = apps.get_model("crm", "ProgramSettings")
    ProgramSettings.objects.get_or_create(id=1)


class Migration(migrations.Migration):
    dependencies = [
        ("crm", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_program_settings, migrations.RunPython.noop),
    ]
