from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponse
import firebase_admin
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from eduApp.settings import firebase


def register(request):
    if request.method == 'POST':
        print(request.POST)
        name = request.POST['name']
        surname = request.POST['surname']
        email = request.POST['email']
        password = request.POST['password']
        password_confirm = request.POST['password_confirm']
        birthdate = request.POST['birthdate']

        if password == password_confirm:
            try:
                user = firebase.auth().create_user_with_email_and_password(email, password)
                # Iniciar sesión al usuario y guardar el token de autenticación en la sesión
                user = firebase.auth().sign_in_with_email_and_password(email, password)
                request.session['uid'] = str(user['idToken'])
                messages.success(request, 'Usuario registrado con éxito')
                return redirect('indexLog')
            except Exception as e:
                print(e)
                messages.error(request, 'Error al crear el usuario')
                return redirect('index')  # Cambiado a 'index'
        else:
            messages.error(request, 'Las contraseñas no coinciden')
            return redirect('index')  # Cambiado a 'index'
    else:
        return render(request, 'index.html')


def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = firebase.auth().sign_in_with_email_and_password(email, password)
            request.session['uid'] = str(user['idToken'])
            return redirect('indexLog')
        except:
            message = "Invalid credentials"
            return render(request, "index.html", {"message": message})
    return render(request, "index.html")


def logout_view(request):
    try:
        del request.session['uid']
    except KeyError:
        pass
    return redirect('index')


# Create your views here.
def index(request):
    return render(request, 'index.html')


def indexLog(request):
    return render(request, 'indexLog.html')


def compraCursos(request):
    return render(request, 'compraCursos.html')


def cursosEstudiante(request):
    return render(request, 'cursosEstudiante.html')


def check_firebase(request):
    try:
        app = firebase_admin.get_app()
        return HttpResponse("Firebase app initialized successfully")
    except ValueError as e:
        return HttpResponse(f"Error initializing Firebase app: {e}")
