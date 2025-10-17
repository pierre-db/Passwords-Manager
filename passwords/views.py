from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
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
    service_list = [entry.service_name for entry in entries]

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
    """Fetch password data for a specific entry"""
    # Validate request parameters
    service_name = request.POST.get('item')

    if not service_name:
        return JsonResponse({'error': 'Invalid request format'}, status=400)

    # Check request limit (configurable via settings)
    request_limit = getattr(settings, 'PASSWORD_MANAGER_REQUEST_LIMIT', 5)
    nb_req = request.session.get('nb_req', 0)
    if nb_req >= request_limit:
        return JsonResponse({'error': 'You have exceeded the allowed number of requests'}, status=429)

    # Increment request counter
    request.session['nb_req'] = nb_req + 1

    try:
        # Get the specific entry by service name, ensuring it belongs to the current user
        entry = PasswordEntry.objects.get(service_name=service_name, user=request.user)

        # Build response data for the specific entry
        user_password = request.session.get('user_password')

        if not user_password:
            return JsonResponse({'error': 'Session expired - please log in again'}, status=401)

        # Generate response
        decrypted_password = entry.decrypt_password(user_password)
        data = {
            'service_name': entry.service_name,
            'username': entry.username,
            'password': decrypted_password,
        }
        if entry.service_url:
            data['service_url'] = entry.service_url
        if entry.comments:
            data['comments'] = entry.comments

        return JsonResponse(data)

    except PasswordEntry.DoesNotExist:
        return JsonResponse({'error': 'Entry not found'}, status=404)
    except Exception:
        return JsonResponse({'error': 'Internal server error'}, status=500)


def logout_view(request):
    """Logout functionality"""
    # Clear sensitive session data
    if 'user_password' in request.session:
        del request.session['user_password']
    logout(request)
    return redirect('login')
