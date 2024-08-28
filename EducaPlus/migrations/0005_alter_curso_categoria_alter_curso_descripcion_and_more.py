# Generated by Django 5.0.3 on 2024-04-06 06:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("EducaPlus", "0004_curso_duracion"),
    ]

    operations = [
        migrations.AlterField(
            model_name="curso",
            name="categoria",
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name="curso",
            name="descripcion",
            field=models.TextField(default="Sin descripción", max_length=1404),
        ),
        migrations.AlterField(
            model_name="curso",
            name="nivel",
            field=models.CharField(max_length=15),
        ),
        migrations.AlterField(
            model_name="curso",
            name="nombre",
            field=models.CharField(max_length=70),
        ),
        migrations.AlterField(
            model_name="curso",
            name="precio",
            field=models.DecimalField(decimal_places=2, max_digits=50),
        ),
    ]