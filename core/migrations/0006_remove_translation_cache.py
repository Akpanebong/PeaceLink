from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("core", "0005_translationcache")]
    operations = [migrations.DeleteModel(name="TranslationCache")]
