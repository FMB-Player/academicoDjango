from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from ..models import Carrera, Materia, Inscripcion, InscripcionCarrera
from ..utils import auto_subscribe_to_available_subjects

User = get_user_model()

class AutoSubscribeToAvailableSubjectsTests(TestCase):
    def setUp(self):
        # Create test user (alumno)
        self.alumno = User.objects.create_user(
            email='alumno@test.com',
            password='testpass123',
            dni=12345678,
            nombre='Test',
            apellido='Alumno',
            rol=User.Rol.ALUMNO
        )
        
        # Create test carrera
        self.carrera = Carrera.objects.create(
            nombre='Ingeniería en Sistemas',
            duracion=5,
            cupo_maximo=100
        )
        
        # Create test materias
        self.materia1 = Materia.objects.create(
            nombre='Matemática I',
            cupo_maximo=30
        )
        self.materia1.carreras.add(self.carrera)
        
        self.materia2 = Materia.objects.create(
            nombre='Programación I',
            cupo_maximo=1  # Limited capacity for testing
        )
        self.materia2.carreras.add(self.carrera)
        
        # Create another student
        self.other_alumno = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            dni=87654321,
            nombre='Other',
            apellido='Student',
            rol=User.Rol.ALUMNO
        )
        
        # Enroll other student in carrera
        with transaction.atomic():
            # Create the enrollment directly
            InscripcionCarrera.objects.create(
                alumno=self.other_alumno,
                carrera=self.carrera
            )
            
            # Then create subject enrollment
            inscripcion = Inscripcion(
                alumno=self.other_alumno,
                materia=self.materia2
            )
            inscripcion.save()  # This will trigger the save validations
    
    def test_auto_subscribe_new_enrollment(self):
        """Test auto-subscription for a new career enrollment"""
        # Enroll student in carrera
        with transaction.atomic():
            inscripcion_carrera = InscripcionCarrera.objects.create(
                alumno=self.alumno,
                carrera=self.carrera
            )
        
        # Call the utility function
        success, skipped, errors = auto_subscribe_to_available_subjects(
            self.alumno, self.carrera.id
        )
        
        # Refresh to get the latest state
        inscripcion_carrera.refresh_from_db()
        
        # Should be subscribed to materia1 (available)
        self.assertEqual(success, 1)
        # Should skip materia2 (full)
        self.assertEqual(skipped, 1)
        self.assertEqual(len(errors), 0)
        
        # Verify the subscription
        self.assertTrue(
            Inscripcion.objects.filter(
                alumno=self.alumno,
                materia=self.materia1,
                is_active=True
            ).exists()
        )
    
    def test_reactivate_inactive_enrollment(self):
        """Test reactivating an inactive enrollment"""
        # First, create and save career enrollment
        with transaction.atomic():
            InscripcionCarrera.objects.create(
                alumno=self.alumno,
                carrera=self.carrera
            )
            
            # Create an inactive enrollment
            inscripcion = Inscripcion(
                alumno=self.alumno,
                materia=self.materia1,
                is_active=False
            )
            inscripcion.save()  # This will trigger the save validations
        
        # Call the utility function
        success, skipped, errors = auto_subscribe_to_available_subjects(
            self.alumno, self.carrera.id
        )
        
        # Should reactivate the existing enrollment
        self.assertEqual(success, 1)
        self.assertEqual(skipped, 1)  # materia2 is full
        self.assertEqual(len(errors), 0)
        
        # Verify the enrollment was reactivated
        inscripcion.refresh_from_db()
        self.assertTrue(inscripcion.is_active)
    
    def test_already_enrolled(self):
        """Test when student is already enrolled in all available subjects"""
        # First, create and save career enrollment
        with transaction.atomic():
            InscripcionCarrera.objects.create(
                alumno=self.alumno,
                carrera=self.carrera
            )
            
            # Enroll student in materia1
            inscripcion = Inscripcion(
                alumno=self.alumno,
                materia=self.materia1
            )
            inscripcion.save()  # This will trigger the save validations
        
        # Call the utility function
        success, skipped, errors = auto_subscribe_to_available_subjects(
            self.alumno, self.carrera.id
        )
        
        # Should skip both (one already enrolled, one full)
        self.assertEqual(success, 0)
        self.assertEqual(skipped, 2)
        self.assertEqual(len(errors), 0)
    
    def test_nonexistent_career(self):
        """Test with a non-existent career ID"""
        # First, create and save career enrollment
        with transaction.atomic():
            InscripcionCarrera.objects.create(
                alumno=self.alumno,
                carrera=self.carrera
            )
        
        # Test with non-existent career ID
        success, skipped, errors = auto_subscribe_to_available_subjects(
            self.alumno, 9999  # Non-existent ID
        )
        
        self.assertEqual(success, 0)
        self.assertEqual(skipped, 0)
        self.assertEqual(len(errors), 1)
        self.assertIn('no encontrada', errors[0])
