from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("screening", "0002_align_abstract_user_fields")]
    operations = [
        migrations.DeleteModel(name="EmailOTP"),
        migrations.RemoveField(model_name="user", name="is_email_verified"),
    ]
