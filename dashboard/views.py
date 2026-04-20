from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from tickets.models import Ticket, Category, Notification, Comment
from django.contrib.auth.models import User
from users.models import Profile
from django.contrib.auth.hashers import make_password
from django.db import transaction
import csv
import json
from django.core.mail import send_mail

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
import random
import string
from django.http import HttpResponse
import csv
from tickets.models import Ticket
from django.http import JsonResponse
from tickets.models import Category

def generate_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def is_staff_member(user):
    if user.is_superuser or user.is_staff:
        return True
    return hasattr(user, 'profile') and user.profile.is_staff_member()

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def dashboard_home(request):
    total_tickets = Ticket.objects.count()
    open_tickets = Ticket.objects.filter(status='open').count()
    resolved_tickets = Ticket.objects.filter(status='resolved').count()
    
    resolved_with_time = Ticket.objects.filter(
        status__in=['resolved', 'closed'],
        resolved_at__isnull=False
    )
    
    if resolved_with_time.exists():
        avg_resolution = resolved_with_time.aggregate(
            avg_time=Avg(
                timezone.now() - timezone.F('created_at')
            )
        )['avg_time']
        avg_resolution_hours = avg_resolution.total_seconds() / 3600 if avg_resolution else 0
    else:
        avg_resolution_hours = 0
    
    tickets_by_status = Ticket.objects.values('status').annotate(count=Count('id'))
    tickets_by_category = Ticket.objects.values('category__name').annotate(count=Count('id'))
    
    recent_tickets = Ticket.objects.all()[:10]
    
    context = {
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'resolved_tickets': resolved_tickets,
        'avg_resolution_hours': round(avg_resolution_hours, 2),
        'tickets_by_status': json.dumps(list(tickets_by_status)),
        'tickets_by_category': json.dumps(list(tickets_by_category)),
        'recent_tickets': recent_tickets,
    }
    
    return render(request, 'dashboard/home.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def all_tickets(request):
    tickets = Ticket.objects.all()
    categories = Category.objects.all()
    search_query = request.GET.get("search", "").strip()

    if search_query:
        tickets = tickets.filter(
            Q(id__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(created_by__username__icontains=search_query)
            # Q(category__name__icontains=search_query)  # change if needed
        ).distinct()

    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    assigned  = request.GET.get('assigned_to')
    category = request.GET.get('category')
    
    if category:
        # tickets = tickets.filter(category__name__iexact=category)
        tickets = tickets.filter(category__name__icontains=category)
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    if assigned == 'me':
        tickets = tickets.filter(assigned_to=request.user)
    elif assigned == 'unassigned':
        tickets = tickets.filter(assigned_to__isnull=True)
    elif assigned:
        tickets = tickets.filter(assigned_to_id=assigned)
    
    staff_users = User.objects.filter(profile__role__in=['admin', 'staff'])
    
    context = {
        'tickets': tickets,
        'staff_users': staff_users,
        'categories': categories,
    }
    
    return render(request, 'dashboard/all_tickets.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def assign_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        if staff_id:
            staff_user = get_object_or_404(User, id=staff_id)
            ticket.assigned_to = staff_user
            ticket.status = 'in_progress'
            ticket.save()
            
            Notification.objects.create(
                user=ticket.created_by,
                ticket=ticket,
                message=f"Your ticket #{ticket.id} has been assigned."
            )
            
            messages.success(request, f'Ticket assigned to {staff_user.username}.')
    
    return redirect('dashboard:all_tickets')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def update_ticket_status(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Ticket.STATUS_CHOICES):
            ticket.status = new_status
            
            if new_status in ['resolved', 'closed'] and not ticket.resolved_at:
                ticket.resolved_at = timezone.now()
            
            ticket.save()
            
            Notification.objects.create(
                user=ticket.created_by,
                ticket=ticket,
                message=f"Your ticket #{ticket.id} status changed to {new_status}."
            )
            
            messages.success(request, 'Ticket status updated.')
    
    return redirect('dashboard:all_tickets')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def manage_users(request):
    print(f"DEBUG: manage_users called by {request.user}")

    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect('dashboard:all_tickets')
    
    # Get all users with ticket stats
    users = User.objects.annotate(
        ticket_count=Count('created_tickets'),
        resolved_count=Count('created_tickets', filter=Q(created_tickets__status='resolved'))
    ).order_by('-date_joined')

    total_users = users.count()
    admins = users.filter(is_superuser=True).count()
    support_staff = users.filter(is_staff=True, is_superuser=False).count()
    customers = users.filter(is_staff=False, is_superuser=False).count()
    active_users = users.filter(is_active=True).count()

    user_list = []
    for user in users:
        rate = 0
        if user.ticket_count > 0:
            rate = round((user.resolved_count / user.ticket_count) * 100)
        user_list.append({'user': user, 'resolution_rate': rate})

    # --- Handle re-opening modal and form data from session ---
    show_add_user_modal = request.session.pop('show_add_user_modal', False)
    form_data = request.session.pop('form_data', {})

    context = {
        'user_list': user_list,
        'total_users': total_users,
        'admins': admins,
        'support_staff': support_staff,
        'customers': customers,
        'active_users': active_users,
        'show_add_user_modal': show_add_user_modal,
        'form_data': form_data,
    }

    return render(request, 'dashboard/manage_users.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def manage_categories(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        category_id = request.POST.get('category_id')
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        icon = request.POST.get('icon', 'bi-tag')  # default icon if none selected
        color = request.POST.get('color', '#007bff')  # default color if none selected

        if action == 'create' and name:
            Category.objects.create(name=name, description=description, icon=icon, color=color)
            messages.success(request, 'Category created successfully.')

        elif action == 'edit' and category_id:
            category = get_object_or_404(Category, id=category_id)
            category.name = name
            category.description = description
            category.icon = icon
            category.color = color
            category.save()
            messages.success(request, 'Category updated successfully.')

        elif action == 'delete' and category_id:
            category = get_object_or_404(Category, id=category_id)
            category.delete()
            messages.success(request, 'Category deleted successfully.')

        return redirect('dashboard:manage_categories')

    # categories = Category.objects.all()
    categories = Category.objects.annotate(
        total_tickets=Count('tickets'),
        open_tickets=Count('tickets', filter=Q(tickets__status='open')),
        closed_tickets=Count(
        'tickets',
        filter=Q(tickets__status='closed') | Q(tickets__status='resolved')
    ),
    )
    return render(request, 'dashboard/manage_categories.html', {'categories': categories})

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
@csrf_exempt
def delete_category(request, category_id):
    if request.method == 'POST':
        try:
            Category.objects.get(id=category_id).delete()
            return JsonResponse({'status': 'success'})
        except Category.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Category not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        icon = request.POST.get('icon', 'bi bi-folder')
        color = request.POST.get('color', '#3b82f6')

        if Category.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': 'Category already exists.'})
        
        cat = Category.objects.create(name=name, description=description, icon=icon, color=color)
        return JsonResponse({'success': True, 'id': cat.id})
    return JsonResponse({'success': False, 'error': 'Invalid request.'})

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def reports(request):
    return render(request, 'dashboard/reports.html')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def export_report(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tickets_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Title', 'Status', 'Priority', 'Created By', 'Assigned To', 'Created At'])
    
    tickets = Ticket.objects.all()
    for ticket in tickets:
        writer.writerow([
            ticket.id,
            ticket.title,
            ticket.status,
            ticket.priority,
            ticket.created_by.username,
            ticket.assigned_to.username if ticket.assigned_to else 'Unassigned',
            ticket.created_at,
            # ticket.resolved_at or 'Not resolved',
        ])
    
    return response

@login_required
def add_user(request):
    print("DEBUG: add_user view called")  # ← ADD
    print(f"DEBUG: Method = {request.method}")  # ← ADD

    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission.")
        return redirect('dashboard:manage_users')

    if request.method == 'POST':
        print("DEBUG: POST data:", request.POST)
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        role = request.POST.get('role')
        # is_staff = request.POST.get('is_staff') == 'on'
        errors = []

        print(f"DEBUG: Creating user → {first_name} {last_name}, email={email}, role={role}")

        if User.objects.filter(email=email).exists():
            print("DEBUG: User already exists!")
            # messages.error(request, 'User with this email already exists.')
            errors.append('User with this email already exists.')
        elif not password or not password2:
            # messages.error(request, 'Both password fields are required.')
            errors.append('Both password fields are required.')
        elif password != password2:
            # messages.error(request, 'Passwords do not match.')
            errors.append('Passwords do not match.')
        elif len(password) < 6:
            # messages.error(request, 'Password must be at least 6 characters.')
            errors.append('Password must be at least 6 characters.')

        if errors:
            for error in errors:
                messages.error(request, error)

            # Store modal flag & form data temporarily in session
            request.session['show_add_user_modal'] = True
            request.session['form_data'] = request.POST.dict()

            return redirect('dashboard:manage_users')
        # else:
        try:
            # with transaction.atomic():
            # password = generate_password()
            # print(f"DEBUG: Generated password: {password}")
            is_staff = False
            is_superuser = False

            if role == 'support':
                is_staff = True
            elif role == 'admin':
                is_staff = True
                is_superuser = True

            print(f"DEBUG: Creating user → {email}, role={role}, staff={is_staff}, super={is_superuser}")
            
            # with transaction.atomic():
            if role == 'admin':
                user = User.objects.create_superuser(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
            else:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=is_staff,
                    is_superuser=is_superuser,
                    is_active=True
                )
            print(f"DEBUG: User created in DB! ID={user.id}")

        #     send_mail(
        #     'Your SupportHub Account',
        #     f'Hello {first_name}!\n\n'
        #     f'Your account has been created.\n\n'
        #     f'Username: {email}\n'
        #     f'Password: {password}\n\n'
        #     f'Login here: http://127.0.0.1:8000/login/\n\n'
        #     f'Please change your password after logging in.',
        #     'no-reply@supporthub.com',
        #     [email],
        #     fail_silently=False,
        # )
            # Optional: send email with temp password
            # messages.success(
            #     request, 
            #     f'User <strong>{email}</strong> created!<br>'
            #     f'Login with: <strong>{email}</strong> | Password: <strong>{password}</strong>'
            #     )
            messages.success(
                request,
                f'''
                    Username: {email} \n
                    Password: {password}\n\n
                    Copy it now — it won't be shown again!
                
                '''
            )
            return redirect('dashboard:manage_users')
        except Exception as e:
            print(f"DEBUG: ERROR → {e}")
            messages.error(request, f'Error: {e}')
        # return redirect('dashboard:manage_users')

    return render(request, 'dashboard/add_user_modal.html')

@csrf_exempt
@login_required
def assign_tickets(request):
    if request.method == 'POST' and hasattr(request.user, 'profile') and request.user.profile.is_staff_member():
        data = json.loads(request.body)
        ticket_ids = data.get('ticket_ids', [])
        staff_id = data.get('staff_id')

        assigned_user = User.objects.filter(id=staff_id, is_staff=True).first()
        if not assigned_user:
            return JsonResponse({'error': 'Invalid staff member'}, status=400)

        Ticket.objects.filter(id__in=ticket_ids).update(assigned_to=assigned_user)

        for t_id in ticket_ids:
            ticket = Ticket.objects.get(id=t_id)
            Comment.objects.create(ticket=ticket, user=request.user, content=f"Ticket assigned to {assigned_user.username}.")
            Notification.objects.create(
                user=assigned_user,
                ticket=ticket,
                message=f"You have been assigned to ticket #{ticket.id} by {request.user.username}."
            )

        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Unauthorized'}, status=403)


@csrf_exempt
@login_required
def delete_tickets(request):
    if request.method == 'POST' and hasattr(request.user, 'profile') and request.user.profile.is_staff_member():
        data = json.loads(request.body)
        ticket_ids = data.get('ticket_ids', [])
        Ticket.objects.filter(id__in=ticket_ids).delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Unauthorized'}, status=403)

@csrf_exempt
@login_required
def api_assign_tickets(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    if not (hasattr(request.user, 'profile') and request.user.profile.is_staff_member()):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    data = json.loads(request.body)
    ticket_ids = data.get('ticket_ids', [])
    staff_id = data.get('staff_id')

    assigned_user = User.objects.filter(id=staff_id, is_staff=True).first()
    if not assigned_user:
        return JsonResponse({'error': 'Invalid staff member'}, status=400)

    for ticket in Ticket.objects.filter(id__in=ticket_ids):
        ticket.assigned_to = assigned_user
        ticket.save()
        Comment.objects.create(ticket=ticket, user=request.user, content=f"Ticket assigned to {assigned_user.username}.")
        Notification.objects.create(
            user=assigned_user,
            ticket=ticket,
            message=f"You have been assigned to ticket #{ticket.id} by {request.user.username}."
        )
    return JsonResponse({'success': True})


@csrf_exempt
@login_required
def api_delete_tickets(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if not (hasattr(request.user, 'profile') and request.user.profile.is_staff_member()):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    data = json.loads(request.body)
    ticket_ids = data.get('ticket_ids', [])
    Ticket.objects.filter(id__in=ticket_ids).delete()
    return JsonResponse({'success': True})

@login_required
@login_required
def staff_search(request):
    query = request.GET.get('q', '')
    users = User.objects.filter(
        Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query),
        is_staff=True
    )
    data = [{'id': u.id, 'name': u.get_full_name() or u.username} for u in users]
    return JsonResponse(data, safe=False)

@login_required
@csrf_exempt
def toggle_user_active(request, user_id):
    """Enable or disable a user account."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        return JsonResponse({'success': True, 'is_active': user.is_active})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


@login_required
@csrf_exempt
def change_user_role(request, user_id):
    """Toggle user role between Support and Customer."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        user = User.objects.get(id=user_id)
        if user.is_superuser:
            return JsonResponse({'error': 'Cannot modify Admin role'}, status=400)
        user.is_staff = not user.is_staff
        user.save()
        return JsonResponse({'success': True, 'is_staff': user.is_staff})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


@login_required
def get_user_details(request, user_id):
    """Fetch user details for edit modal."""
    try:
        user = User.objects.get(id=user_id)
        data = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        return JsonResponse({'success': True, 'data': data})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
# @require_POST
@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def update_user_details(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method.'})

    try:
        user = User.objects.get(id=user_id)
        data = json.loads(request.body.decode('utf-8'))

        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)
        user.username = data.get('username',user.username)
        user.save()

        if "password" in data and data["password"].strip():
            user.set_password(data["password"].strip())

        user.save()
        
        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def delete_user(request, user_id):
    if request.method == "POST":
        try:
            user = User.objects.get(pk=user_id)
            user.delete()
            return JsonResponse({"success": True})
        except User.DoesNotExist:
            return JsonResponse({"success": False, "error": "User not found"})
    return JsonResponse({"success": False, "error": "Invalid request"})