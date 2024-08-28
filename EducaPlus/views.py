import os
import re
import tempfile
from datetime import datetime
from urllib.parse import quote
import base64

from PIL import Image
from botocore.exceptions import BotoCoreError, ClientError
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import Group, User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from moviepy.editor import VideoFileClip
from unidecode import unidecode

from spaces import client, space_name
from .decorators import group_required
from .models import Student, Instructor, Curso, Compra, Cart, Seccion, Archivo


def buscar_cursos(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        q = request.GET.get('q', '')
        cursos = Curso.objects.filter(nombre__icontains=q)
        resultados = [{'id': curso.id, 'nombre': curso.nombre} for curso in cursos]
        return JsonResponse(resultados, safe=False)
    return JsonResponse({'error': 'Invalid request'}, status=400)


def search_courses(request):
    if request.method == "GET":
        query = request.GET.get('q', '')
        instructor = Instructor.objects.get(user=request.user)
        if query:
            cursos = Curso.objects.filter(nombre__icontains=query, instructor=instructor)
        else:
            cursos = Curso.objects.filter(instructor=instructor)
        cursos_list = list(cursos.values('nombre', 'descripcion', 'id'))
        return JsonResponse({'cursos': cursos_list})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def verificar_correo_teach(request):
    if request.method == 'POST':
        correo = request.POST.get('correo', None)
        if correo:
            try:
                user_obj = User.objects.get(email=correo)
                return JsonResponse({'existe': True})
            except User.DoesNotExist:
                return JsonResponse({'existe': False})
        else:
            return JsonResponse(
                {'error': 'Correo no proporcionado en la solicitud'},
                status=400)

    return JsonResponse({'error': 'Solicitud inválida'}, status=400)


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Obtener o inicializar el contador de intentos fallidos
        failed_attempts = request.session.get('failed_attempts', 0)

        user = authenticate(request, username=email, password=password)
        if user is not None:
            request.session['failed_attempts'] = 0  # Reiniciar el contador en caso de éxito
            if user.groups.filter(name='Instructores').exists():
                login(request, user)
                return JsonResponse({'success': True, 'userType': 'Instructor'})
            elif user.groups.filter(name='Estudiantes').exists():
                login(request, user)
                return JsonResponse({'success': True, 'userType': 'Estudiante'})
        else:
            # Incrementar el contador de intentos fallidos
            failed_attempts += 1
            request.session['failed_attempts'] = failed_attempts

            # Verificar el tipo de error
            try:
                existing_user = User.objects.get(email=email)
                if existing_user:
                    if failed_attempts >= 5:
                        return JsonResponse({'success': False, 'errorType': 'tooManyAttempts'})
                    return JsonResponse({'success': False, 'errorType': 'incorrectPassword'})
            except User.DoesNotExist:
                if failed_attempts >= 5:
                    return JsonResponse({'success': False, 'errorType': 'tooManyAttempts'})
                return JsonResponse({'success': False, 'errorType': 'emailNotFound'})

    return JsonResponse({'success': False, 'errorType': 'incorrectCredentials'})


@csrf_exempt
def verificar_correo(request):
    if request.method == 'POST':
        correo = request.POST.get('correo', None)
        if correo:
            try:
                user_obj = User.objects.get(email=correo)
                return JsonResponse({'existe': True})
            except User.DoesNotExist:
                return JsonResponse({'existe': False})
        else:
            return JsonResponse(
                {'error': 'Correo no proporcionado en la solicitud'},
                status=400)

    return JsonResponse({'error': 'Solicitud inválida'}, status=400)


def register(request):
    if request.method == 'POST':
        name = request.POST['name']
        surname = request.POST['surname']
        email = request.POST['email']
        password = request.POST['password']
        password_confirm = request.POST['password_confirm']
        birthdate = request.POST['birthdate']

        if password == password_confirm:
            if User.objects.filter(email=email).exists():
                messages.error(request, 'El correo electrónico ya está en uso')
                return redirect('index')
            else:
                user = User.objects.create_user(username=email,
                                                password=password, email=email,
                                                first_name=name,
                                                last_name=surname)
                Student.objects.create(user=user, birthdate=birthdate)
                user.save()
                group = Group.objects.get(name='Estudiantes')
                user.groups.add(group)
                login(request, user)
                messages.success(request, 'Te has registrado exitosamente')
                return redirect('indexLog')
        else:
            messages.error(request, 'Las contraseñas no coinciden')
            return redirect('index')
    else:
        return render(request, 'index.html')


def teach(request):
    if request.method == 'POST':
        name = request.POST['name']
        surname = request.POST['surname']
        email = request.POST['email']
        password = request.POST['password']
        password_confirm = request.POST['passwordConfirm']
        birthdate = request.POST['birthdate1']
        specialization = request.POST['specialization']

        if password == password_confirm:
            if User.objects.filter(username=email).exists():
                messages.error(request, 'El correo electrónico ya está en uso')
                return redirect('index')
            else:
                user = User.objects.create_user(username=email,
                                                password=password, email=email,
                                                first_name=name,
                                                last_name=surname)
                Instructor.objects.create(user=user, birthdate=birthdate,
                                          specialization=specialization)
                user.save()
                group = Group.objects.get(name='Instructores')
                user.groups.add(group)
                login(request, user)
                messages.success(request,
                                 'Te has registrado exitosamente como '
                                 'instructor')
                return redirect('crearCursos')
        else:
            messages.error(request, 'Las contraseñas no coinciden')
            return redirect('index')
    else:
        return render(request, 'index.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente')
    return redirect('index')


def index(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='Estudiantes').exists():
            return redirect('indexLog')
        elif request.user.groups.filter(name='Instructores').exists():
            return redirect('crearCursos')

    categorias = Curso.objects.values_list('categoria', flat=True).distinct().order_by('categoria')
    cursos = Curso.objects.all().order_by('nombre')
    return render(request, 'index.html',
                  {'cursos': cursos, 'categorias': categorias})


@login_required
@group_required('Estudiantes', redirect_route='crearCursos')
def indexLog(request):
    categorias = Curso.objects.values_list('categoria', flat=True).distinct().order_by('categoria')
    cursos = Curso.objects.all().order_by('nombre')
    return render(request, 'indexLog.html',
                  {'cursos': cursos, 'categorias': categorias})


@login_required
@group_required('Estudiantes', redirect_route='crearCursos')
def compraCursos(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    return render(request, 'compraCursos.html', {'curso': curso})


@login_required
@group_required('Estudiantes', redirect_route='crearCursos')
def cursosEstudiante(request):
    compras = Compra.objects.filter(estudiante_id=request.user.student.id).order_by('-fecha_transaccion')
    cursos = [compra.curso for compra in compras]
    return render(request, 'cursosEstudiante.html', {'cursos': cursos})


@login_required
@group_required('Instructores', redirect_route='indexLog')
def crearCursos(request):
    cursos_del_instructor = Curso.objects.filter(instructor__user=request.user).order_by('-id')
    return render(request, 'crearCurso.html',
                  {'cursos_del_instructor': cursos_del_instructor})


@login_required
@group_required('Instructores', redirect_route='indexLog')
def crearDatosCursos(request):
    return render(request, 'crearDatosCurso.html')


@login_required
@group_required('Instructores', redirect_route='indexLog')
def crear_curso(request):
    if request.method == 'POST':
        nombre = request.POST['courseName']
        descripcion = request.POST['courseDescription']
        categoria = request.POST['courseCategory']
        duracion = request.POST['courseDuration']
        nivel = request.POST['courseDifficulty']
        coursepayment = request.POST['coursePayment']
        precio = request.POST['courseCost'] if coursepayment == 'pago' else 0.0
        curso = Curso(nombre=nombre, descripcion=descripcion,
                      categoria=categoria, duracion=duracion,
                      nivel=nivel, precio=precio,
                      instructor=request.user.instructor)
        curso.save()

        messages.success(request, 'Curso creado exitosamente')
        return redirect('crearCursos')
    else:
        return render(request, 'crearCurso.html')


@login_required
@group_required('Estudiantes', redirect_route='crearCursos')
@csrf_exempt
def procesar_pago(request):
    if request.method == 'POST':
        curso_id = request.POST.get('curso_id')
        estudiante_id = request.POST.get('estudiante_id')

        if Compra.objects.filter(estudiante_id=estudiante_id,
                                 curso_id=curso_id).exists():
            return JsonResponse(
                {'status': 'failed', 'message': 'Ya has comprado este curso'})

        # Si el pago es exitoso, crea una nueva instancia de Compra
        compra = Compra(estudiante_id=estudiante_id, curso_id=curso_id)
        compra.save()

        messages.success(request, 'Pago procesado exitosamente')
        return redirect('cursosEstudiante')
    else:
        return JsonResponse({'status': 'failed'})


@login_required
def add_cart(request, curso_id):
    # Obtiene el carrito de compras del usuario actual
    cart, created = Cart.objects.get_or_create(student=request.user.student)

    # Obtiene el curso que se va a agregar al carrito
    curso = get_object_or_404(Curso, id=curso_id)

    # Verifica si el curso ya está en el carrito
    if cart.courses.filter(id=curso_id).exists():
        # Si el curso ya está en el carrito, devuelve un error
        return JsonResponse(
            {'success': False, 'error': 'El curso ya está en el carrito'})

    # Si el curso no está en el carrito, lo agrega
    cart.add_course(curso)

    # Devuelve una respuesta JSON con el número de cursos en el carrito
    return JsonResponse(
        {'success': True, 'cart_count': cart.courses.count()})


@login_required
def obtener_contador_carrito(request):
    # Obtiene el carrito de compras del usuario actual
    cart, created = Cart.objects.get_or_create(student=request.user.student)

    # Devuelve el contador del carrito como una respuesta JSON
    return JsonResponse({'success': True, 'cart_count': cart.courses.count()})


def olvideContraseña(request):
    return render(request, 'olvideContraseña.html')


def correoEnviar(request):
    if request.method == 'POST':
        email = request.POST['email']
        user = get_user_model().objects.filter(email=email).first()
        token_generator = PasswordResetTokenGenerator()
        if user:
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            current_site = get_current_site(request)
            mail_subject = 'Restablecer contraseña'
            message = render_to_string('restablecerContraseña.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': uid,
                'token': token,
            })
            send_mail(mail_subject, '', 'eduplus720@gmail.com', [email],
                      html_message=message)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
    except (
            TypeError, ValueError, OverflowError,
            get_user_model().DoesNotExist):
        user = None

    token_generator = PasswordResetTokenGenerator()
    if user is not None and token_generator.check_token(user, token):
        # El token es válido, mostrar el formulario de restablecimiento de contraseña
        return render(request, 'nuevaContraseña.html', {'validlink': True, 'uid':
            uidb64, 'token': token})
    else:
        # El token no es válido, mostrar un mensaje de error
        return render(request, 'nuevaContraseña.html', {'validlink': False})


def change_password(request, uidb64):
    if request.method == 'POST':
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if new_password != confirm_password:
            return HttpResponse('Las contraseñas no coinciden', status=400)

        # Validaciones de contraseña
        if not re.search(r'[A-Z]', new_password):
            return HttpResponse('La contraseña debe contener al menos una letra mayúscula', status=400)
        if not re.search(r'[a-z]', new_password):
            return HttpResponse('La contraseña debe contener al menos una letra minúscula', status=400)
        if not re.search(r'[0-9]', new_password):
            return HttpResponse('La contraseña debe contener al menos un número', status=400)
        if not re.search(r'[ `!@#$%^&*()_+\-=\[\]{};:"\\|,.<>/?~¡¿ü]', new_password):
            return HttpResponse('La contraseña debe contener al menos un carácter especial', status=400)
        if len(new_password) < 8 or len(new_password) > 128:
            return HttpResponse('La longitud de la contraseña debe estar entre 8 y 128 caracteres', status=400)

        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)

        # Verifica que la nueva contraseña no sea la misma que la antigua
        if check_password(new_password, user.password):
            return HttpResponse('La nueva contraseña no puede ser la misma que la antigua', status=400)

        user.password = make_password(new_password)
        user.save()

        messages.success(request, 'Contraseña actualizada exitosamente', extra_tags='password_changed')

        return redirect('index')

    return HttpResponse('Método no permitido', status=405)


@csrf_exempt
def check_same_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        uidb64 = request.POST.get('uidb64')

        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)

        if check_password(new_password, user.password):
            return JsonResponse({'same_password': True})
        else:
            return JsonResponse({'same_password': False})

    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
def obtener_datos_usuario(request):
    # Obtener el estudiante actual
    estudiante = request.user.student

    # Verificar si el estudiante existe
    if estudiante:
        # Convertir los datos binarios de la imagen en una cadena base64
        if estudiante.foto_perfil:
            foto_perfil_base64 = base64.b64encode(estudiante.foto_perfil).decode('utf-8')
            # Crear una URL de datos para la imagen
            foto_perfil_url = f'data:image/jpeg;base64,{foto_perfil_base64}'
        else:
            foto_perfil_url = None

        data = {
            'nombre': request.user.first_name,
            'apellido': request.user.last_name,
            'fecha_nacimiento': estudiante.birthdate.strftime('%Y-%m-%d'),
            'foto_perfil': foto_perfil_url,
        }
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'Invalid Method'})


@login_required
def obtener_datos_instructor(request):
    instructor = request.user.instructor

    if instructor:
        # Convertir los datos binarios de la imagen en una cadena base64
        if instructor.foto_perfil:
            foto_perfil_base64 = base64.b64encode(instructor.foto_perfil).decode('utf-8')
            # Crear una URL de datos para la imagen
            foto_perfil_url = f'data:image/jpeg;base64,{foto_perfil_base64}'
        else:
            foto_perfil_url = None

        data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'date_of_birth': instructor.birthdate.strftime('%Y-%m-%d'),
            'specialization': instructor.specialization,
            'foto_perfil': foto_perfil_url,
        }
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'Invalid Method'})


@login_required
def updateEstudiante(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        foto_perfil = request.FILES.get('foto_perfil')  # Recibir el archivo de la foto de perfil

        # Obtener el estudiante actual
        estudiante = request.user.student

        # Actualizar los datos del estudiante
        request.user.first_name = nombre
        request.user.last_name = apellido
        estudiante.birthdate = fecha_nacimiento

        # Leer el archivo de la imagen y guardar sus bytes en la base de datos
        if foto_perfil:
            foto_perfil_bytes = foto_perfil.read()
            estudiante.foto_perfil = foto_perfil_bytes

        request.user.save()
        estudiante.save()

        # Agregar mensaje de éxito
        messages.success(request, '¡Los cambios se guardaron correctamente!')

        # Redirigir al usuario a la página que desees
        return redirect('indexLog')
    else:
        return JsonResponse({'error': 'Invalid Method'})


@login_required
def updateInstructor(request):
    if request.method == 'POST':
        # Obtener el usuario y el instructor actual asociado a ese usuario
        user = request.user
        instructor = user.instructor

        # Actualizar los datos del usuario e instructor con los datos del formulario
        user.first_name = request.POST.get('firstName', '')
        user.last_name = request.POST.get('lastName', '')
        foto_perfil = request.FILES.get('foto_perfil')  # Recibir el archivo de la foto de perfil

        # Leer el archivo de la imagen y guardar sus bytes en la base de datos
        if foto_perfil:
            foto_perfil_bytes = foto_perfil.read()
            instructor.foto_perfil = foto_perfil_bytes

        user.save()
        instructor.save()

        # Convertir la fecha de nacimiento a formato de fecha
        fecha_nacimiento_str = request.POST.get('dob', '')
        try:
            fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
            instructor.birthdate = fecha_nacimiento
            instructor.save()  # Guardar el objeto instructor después de cambiar la fecha de nacimiento
        except ValueError:
            print(f"Error: La fecha {fecha_nacimiento_str} no está en el formato correcto 'YYYY-MM-DD'")

        # Actualizar la especialización del instructor
        instructor.specialization = request.POST.get('specialization', '')
        instructor.save()

        # Agregar mensaje de éxito utilizando el framework de mensajes de Django
        messages.success(request, '¡Los cambios se guardaron correctamente!')

        # Redirigir al usuario a la página deseada
        return redirect('indexLog')
    else:
        # Devolver una respuesta HTTP con un código de estado 405 (Método no permitido)
        return HttpResponseNotAllowed(['POST'])


@login_required
@group_required('Instructores', redirect_route='indexLog')
def obtenerDatosCurso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    # Verificar si el usuario actual es el instructor del curso
    if request.user.instructor != curso.instructor:
        # Si no es el instructor, devolver una respuesta HTTP 403 (Prohibido)
        return HttpResponseForbidden()

    return render(request, 'editarDatosCurso.html', {'curso': curso})


@login_required
@group_required('Instructores', redirect_route='indexLog')
def editarCurso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    # Verificar si el usuario actual es el instructor del curso
    if request.user.instructor != curso.instructor:
        # Si no es el instructor, devolver una respuesta HTTP 403 (Prohibido)
        return HttpResponseForbidden()

    if request.method == 'POST':
        # Obtener los valores del POST request
        nombre = request.POST['courseName']
        descripcion = request.POST['courseDescription']
        categoria = request.POST['courseCategory']
        duracion = float(request.POST['courseDuration'])
        nivel = request.POST['courseDifficulty']
        precio = float(request.POST['courseCost']) if request.POST['coursePayment'] == 'pago' else 0.0

        # Verificar si se hicieron cambios
        cambios_realizados = False
        if curso.nombre != nombre:
            curso.nombre = nombre
            cambios_realizados = True
        if curso.descripcion != descripcion:
            curso.descripcion = descripcion
            cambios_realizados = True
        if curso.categoria != categoria:
            curso.categoria = categoria
            cambios_realizados = True
        if curso.duracion != duracion:
            curso.duracion = duracion
            cambios_realizados = True
        if curso.nivel != nivel:
            curso.nivel = nivel
            cambios_realizados = True
        if curso.precio is None:
            curso.precio = 0.0
        if curso.precio != precio:
            curso.precio = precio
            cambios_realizados = True

        if cambios_realizados:
            # Si se hicieron cambios, guardar el objeto y mostrar el mensaje
            curso.save()
            messages.success(request, 'Curso actualizado exitosamente', extra_tags='curso_actualizado')

        return redirect('crearCursos')
    else:
        return render(request, 'editarDatosCurso.html', {'curso': curso})


@login_required
def agregarContenido(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    secciones = Seccion.objects.filter(curso_id=curso_id)
    if request.method == 'POST':
        section_id = request.POST['section_id']
        try:
            section = Seccion.objects.get(id=section_id)
        except Seccion.MultipleObjectsReturned:
            section = Seccion.objects.filter(id=section_id).first()
        error_messages = []  # Lista para almacenar los mensajes de error
        for uploaded_file in request.FILES.getlist('file'):
            file_name = uploaded_file.name
            response = upload_to_course_bucket(uploaded_file, curso_id, section_id, section.nombre, file_name)
            if 'error' in response:
                error_messages.append(response['error'])  # Agregar el mensaje de error a la lista
            else:
                messages.success(request, f'Archivo {file_name} subido exitosamente', extra_tags='archivo_subido')
        for error in error_messages:  # Mostrar todos los mensajes de error
            messages.error(request, error)
        return redirect('agregar_contenido', curso_id=curso_id)
    return render(request, 'agregarContenido.html', {'secciones': secciones, 'curso': curso})


def upload_to_course_bucket(uploaded_file, curso_id, section_id, section_name, file_name):
    bucket_name = space_name
    file_name = sanitize_filename(file_name)
    key = f'{curso_id}/{section_name}/{section_id}/{file_name}'
    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    file_extension = os.path.splitext(file_name)[1]
    if file_extension in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
        file_type = 'imagen'
        image = Image.open(uploaded_file)
        width, height = image.size
        if width < 1024 or height < 768:
            return {'error': f"La resolución de la imagen {file_name} debe ser al menos 1024x768"}
    elif file_extension in ['.mp4', '.MP4', '.mpeg', '.MPEG']:
        file_type = 'video'
        if isinstance(uploaded_file, InMemoryUploadedFile):
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(file_bytes)
            temp_file.close()
            clip = VideoFileClip(temp_file.name)
        else:
            clip = VideoFileClip(uploaded_file.temporary_file_path())
        if clip.size[1] < 480:
            return {'error': f"La resolución del video {file_name} debe ser al menos 480p"}
    elif file_extension in ['.mp3']:
        file_type = 'audio'
    elif file_extension in ['.ppt']:
        file_type = 'ppt'
    elif file_extension in ['.pdf']:
        file_type = 'pdf'
    else:
        return {'error': f"Tipo de archivo {file_extension} no soportado"}
    try:
        client.put_object(Body=file_bytes, Bucket=bucket_name, Key=key, ACL='public-read')
        url = f"https://{bucket_name}.nyc3.cdn.digitaloceanspaces.com/contenidoo/{key}"
        seccion = Seccion.objects.get(id=section_id)
        Archivo.objects.create(nombre=file_name, url=url, tipo=file_type, seccion=seccion)
        return {'success': url}
    except (BotoCoreError, ClientError) as error:
        return {'error': str(error)}


@login_required
@group_required('Instructores', redirect_route='indexLog')
def agregarSeccion(request, curso_id):
    if request.method == 'POST':
        # Obtener los datos del formulario
        section_name = request.POST.get('section_name')

        # Check if section_name is None or empty
        if not section_name:
            return HttpResponse('section_name not provided', status=400)

        # Obtener el curso
        curso = get_object_or_404(Curso, id=curso_id)

        # Crear una nueva sección
        seccion = Seccion(nombre=section_name, curso=curso)

        # Guardar la sección en la base de datos
        seccion.save()

        messages.success(request, 'Nueva sección agregada.', extra_tags='seccion_agregada')

        # Redirigir al usuario a la página de agregar contenido
        return redirect('agregar_contenido', curso_id=curso_id)
    else:
        # Si el método no es POST, devolver una respuesta HTTP 405 (Método no permitido)
        return HttpResponseNotAllowed(['POST'])


def eliminar_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    try:
        # Define the bucket and the prefix for the objects to delete
        bucket_name = space_name
        prefix = f"{curso_id}/"

        # List all objects in the bucket under the course folder
        objects_to_delete = client.list_objects(Bucket=bucket_name, Prefix=prefix)

        # Iterate over each object and delete it
        for obj in objects_to_delete.get('Contents', []):
            client.delete_object(Bucket=bucket_name, Key=obj['Key'])

        # Delete the course from the database
        curso.delete()

        return JsonResponse({'success': True})
    except (BotoCoreError, ClientError) as e:
        # If there was an error with DigitalOcean Spaces, return an error
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        # If there was an error with deleting the course from the database, return an error
        return JsonResponse({'success': False, 'error': str(e)})


def sanitize_filename(filename):
    base_name, extension = os.path.splitext(filename)
    normalized_base_name = unidecode(base_name)  # Normalizar la cadena de texto
    safe_base_name = re.sub(r'\W+', '_', normalized_base_name)
    safe_filename = safe_base_name + extension
    return quote(safe_filename, safe='')


@login_required
def get_student_image(request):
    estudiante = request.user.student

    if estudiante:
        # Convertir los datos binarios de la imagen en una cadena base64
        if estudiante.foto_perfil:
            foto_perfil_base64 = base64.b64encode(estudiante.foto_perfil).decode('utf-8')
            # Crear una URL de datos para la imagen
            foto_perfil_url = f'data:image/jpeg;base64,{foto_perfil_base64}'
        else:
            foto_perfil_url = None

        data = {
            'foto_perfil': foto_perfil_url,
        }
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'Invalid Method'})


@login_required
def get_instructor_image(request):
    instructor = request.user.instructor

    if instructor:
        # Convertir los datos binarios de la imagen en una cadena base64
        if instructor.foto_perfil:
            foto_perfil_base64 = base64.b64encode(instructor.foto_perfil).decode('utf-8')
            # Crear una URL de datos para la imagen
            foto_perfil_url = f'data:image/jpeg;base64,{foto_perfil_base64}'
        else:
            foto_perfil_url = None

        data = {
            'foto_perfil': foto_perfil_url,
        }
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'Invalid Method'})
