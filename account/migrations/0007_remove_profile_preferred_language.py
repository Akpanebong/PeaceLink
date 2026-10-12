from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("account", "0006_remove_profile_country_code_alter_profile_phone")]
    operations = [migrations.RemoveField(model_name="profile", name="preferred_language")]
