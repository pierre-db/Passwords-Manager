from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import PasswordEntry


def login_view(request):
    """Main login page"""
    if request.user.is_authenticated:
        return redirect('index')

    return render(request, 'passwords/login.html')


@csrf_exempt
@require_POST
def check_login(request):
    """Check login credentials using Django authentication"""
    username = request.POST.get('login', '')
    password = request.POST.get('password', '')

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        request.session['nb_req'] = 0  # Reset request counter
        # Store encrypted password for decryption (security note: this is still a session-based approach)
        # In production, consider using a more secure method like requiring password re-entry for sensitive operations
        request.session['user_password'] = password
        return redirect('index')
    else:
        return render(request, 'passwords/login.html', {'error': 'Invalid credentials'})


@login_required
def index_view(request):
    """Main password manager page"""
    # Get all password entries for the current user to build service list
    entries = PasswordEntry.objects.filter(user=request.user).order_by('service_name')
    service_list = [entry.service_name.lower() for entry in entries]

    context = {
        'categories': service_list,  # Keep same template variable name for compatibility
        'nb_categories': len(service_list)
    }

    # Set session data
    request.session['nb_group'] = len(service_list)

    return render(request, 'passwords/index.html', context)


@csrf_exempt
@require_POST
@login_required
def fetch_data(request):
    """Fetch password data for a category"""
    # Validate request parameters
    item = request.POST.get('item')

    if not item:
        return HttpResponse('Format de requette erroné', status=400)

    try:
        item = int(item)
    except ValueError:
        return HttpResponse('Format de requette erroné', status=400)

    # Check request limit (5 requests max like original)
    nb_req = request.session.get('nb_req', 0)
    if nb_req >= 5:
        return HttpResponse('Vous avez dépassé le nombre de requettes autorisées', status=429)

    # Get user's services
    entries = list(PasswordEntry.objects.filter(user=request.user).order_by('service_name'))

    # Validate item range
    if item >= len(entries):
        return HttpResponse('Format de requette erroné', status=400)

    # Increment request counter
    request.session['nb_req'] = nb_req + 1

    try:
        # Get the specific entry by index
        entry = entries[item]

        # Build response data for the specific entry
        user_password = request.session.get('user_password')

        if not user_password:
            return HttpResponse('Session expirée - reconnectez-vous', status=401)

        decrypted_password = entry.decrypt_password(user_password)
        data = f'<strong>{entry.service_name}</strong><br>'
        if entry.service_url:
            data += f'URL: <a href="{entry.service_url}" target="_blank">{entry.service_url}</a><br>'
        data += f'Username: {entry.username}<br>'
        data += f'Password: {decrypted_password}<br>'
        if entry.comments:
            data += f'Notes: {entry.comments}<br>'

        return HttpResponse(data)

    except Exception:
        return HttpResponse('Le fichier est introuvable ou incompatible', status=500)


def logout_view(request):
    """Logout functionality"""
    # Clear sensitive session data
    if 'user_password' in request.session:
        del request.session['user_password']
    logout(request)
    return redirect('login')
