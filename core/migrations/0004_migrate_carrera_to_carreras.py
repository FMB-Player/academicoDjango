from django.db import migrations


def migrate_carrera_to_carreras(apps, schema_editor):
    """
    Migrate data from the old carrera ForeignKey to the new carreras ManyToManyField.
    """
    Materia = apps.get_model('core', 'Materia')
    
    # For each materia, add its carrera to the carreras many-to-many field
    for materia in Materia.objects.all():
        # Use the old carrera field to add to the new carreras field
        if hasattr(materia, 'carrera'):
            # Get the carrera from the old field
            carrera = materia.carrera
            if carrera:
                # Add the carrera to the many-to-many field
                materia.carreras.add(carrera)


def reverse_migrate(apps, schema_editor):
    """
    Reverse migration: move data back from carreras to carrera.
    Note: This is not perfect as we might have multiple carreras, but we'll take the first one.
    """
    Materia = apps.get_model('core', 'Materia')
    
    for materia in Materia.objects.all():
        # Get the first carrera from the many-to-many field
        if materia.carreras.exists():
            # Set the old carrera field to the first carrera in the many-to-many
            carrera = materia.carreras.first()
            materia.carrera = carrera
            materia.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_materia_options_alter_materia_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(
            migrate_carrera_to_carreras,
            reverse_code=reverse_migrate,
        ),
    ]
