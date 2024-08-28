from django.urls import path
from django.conf import settings
from django.conf.urls.static import static


from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('compraCursos/<int:curso_id>/', views.compraCursos, name='compraCursos'),
    path('cursosEstudiante/', views.cursosEstudiante, name='cursosEstudiante'),
    path('indexLog/', views.indexLog, name='indexLog'),
    path('crearCursos/', views.crearCursos, name='crearCursos'),
    path('crearDatosCursos/', views.crearDatosCursos, name='crearDatosCursos'),
    path('register/', views.register, name='register'),
    path('teach/', views.teach, name='teach'),
    path('logout/', views.logout_view, name='logout'),
    path('crear_curso/', views.crear_curso, name='crear_curso'),
    path('procesar_pago/', views.procesar_pago, name='procesar_pago'),
    path('api/verificar-correo/', views.verificar_correo, name='verificar_correo'),
    path('add_cart/<int:curso_id>/', views.add_cart, name='add_cart'),
    path('obtener_contador_carrito/', views.obtener_contador_carrito, name='obtener_contador_carrito'),
    path('login/', views.login_view, name='login'),
    path('recuperarContraseña/', views.olvideContraseña, name='olvide_contraseña'),
    path('correoEnviar/', views.correoEnviar, name='correoEnviar'),
    path('password_reset_confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('change_password/<str:uidb64>/', views.change_password, name='change_password'),
    path('check_same_password/', views.check_same_password, name='check_same_password'),
    path('api/verificar-correo-teach/', views.verificar_correo_teach, name='verificar_correo_teach'),
    path('obtener-datos-usuario/', views.obtener_datos_usuario, name='obtener_datos_usuario'),
    path('obtener-datos-instructor/', views.obtener_datos_instructor, name='obtener_datos_instructor'),
    path('updateEstudiante/', views.updateEstudiante, name='updateEstudiante'),
    path('updateInstructor/', views.updateInstructor, name='updateInstructor'),
    path('curso/editar/<int:curso_id>/', views.editarCurso, name='editar_curso'),
    path('curso/<int:curso_id>/obtenerDatosCurso/', views.obtenerDatosCurso, name='obtenerDatosCurso'),
    path('agregarContenido/<int:curso_id>/', views.agregarContenido, name='agregar_contenido'),
    path('add_section/<int:curso_id>/', views.agregarSeccion, name='add_section'),
    path('eliminar_curso/<int:curso_id>/', views.eliminar_curso, name='eliminar_curso'),
    path('search/', views.search_courses, name='search_courses'),
    path('buscar_cursos/', views.buscar_cursos, name='buscar_cursos'),
    path('indexLog/', views.indexLog, name='indexLog'),
    path('cursosEstudiante/', views.cursosEstudiante, name='cursosEstudiante'),
    path('get_student_image/', views.get_student_image, name='get_student_image'),
    path('get_instructor_image/', views.get_instructor_image, name='get_instructor_image'),
]