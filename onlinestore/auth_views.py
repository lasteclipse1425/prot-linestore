import json

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import AuthenticationForm
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _

from .forms import RegisterForm

User = get_user_model()


def register(request):
    """Create an account and establish its Django session."""
    if request.user.is_authenticated:
        return redirect('onlinestore:profile')

    form = RegisterForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password1'],
                    first_name=form.cleaned_data.get('first_name', '').strip(),
                    last_name=form.cleaned_data.get('last_name', '').strip(),
                )
        except IntegrityError:
            form.add_error(
                None,
                _('Could not create the account. This username may already be in use.'),
            )
        else:
            login(request, user)
            messages.success(request, _('Account %(username)s was created successfully.') % {'username': user.username})
            return redirect('onlinestore:profile')

    return render(request, 'user/register.html', {'form': form})


def register_api(request):
    """Register a user from a CSRF-protected JSON request and issue a session."""
    if request.method != 'POST':
        return JsonResponse({'detail': 'Only POST requests are supported.'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({'detail': 'Invalid JSON payload.'}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({'detail': 'The JSON payload must be an object.'}, status=400)

    form = RegisterForm(payload)
    if not form.is_valid():
        return JsonResponse(
            {'detail': 'Registration failed.', 'errors': form.errors.get_json_data()},
            status=400,
        )

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data.get('first_name', '').strip(),
                last_name=form.cleaned_data.get('last_name', '').strip(),
            )
    except IntegrityError:
        return JsonResponse(
            {'detail': 'The username is already in use.'},
            status=400,
        )

    login(request, user)
    return JsonResponse(
        {
            'detail': 'Registration successful.',
            'user': {
                'id': user.pk,
                'username': user.username,
                'email': user.email,
            },
        },
        status=201,
    )


def sign_in(request):
    """Authenticate credentials and safely redirect within this site."""
    if request.user.is_authenticated:
        return redirect('onlinestore:profile')

    form = AuthenticationForm(
        request,
        data=request.POST if request.method == 'POST' else None,
    )
    form.fields['username'].widget.attrs.update({
        'class': 'form-control',
        'id': 'inputUsername',
        'placeholder': _('Username'),
        'autocomplete': 'username',
    })
    form.fields['password'].widget.attrs.update({
        'class': 'form-control',
        'id': 'inputPassword',
        'placeholder': _('Password'),
        'autocomplete': 'current-password',
    })
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect('onlinestore:profile')

    return render(
        request,
        'user/login.html',
        {'form': form, 'next': request.POST.get('next') or request.GET.get('next', '')},
    )
