from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Ticket, Comment, Notification, Category
from .forms import TicketForm, CommentForm
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count
from datetime import date
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(created_by=request.user)
    return render(request, 'tickets/my_tickets.html', {'tickets': tickets})

@login_required
def create_ticket(request):
    if request.method == 'POST':
        print("POST received")
        print("\n" + "="*50)
        print("RAW POST DATA:")
        for key, value in request.POST.items():
            print(f"  {key}: {value}")
        print("="*50 + "\n")
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            print("Form valid")
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            # print("Ticket saved:", ticket.id, ticket.subject)
            messages.success(request, 'Ticket created successfully!')
            return redirect('tickets:ticket_detail', ticket_id=ticket.id)
        else:
            print("Form errors:", form.errors)
    else:
        print("GET request - showing form")
        form = TicketForm()
    return render(request, 'tickets/create_ticket.html', {'form': form})

@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    staff_list = User.objects.filter(is_staff=True, is_active=True)
    
    if not (ticket.created_by == request.user or 
            (hasattr(request.user, 'profile') and request.user.profile.is_staff_member())):
        messages.error(request, 'You do not have permission to view this ticket.')
        return redirect('tickets:my_tickets')
    
    if request.method == 'POST':
        if 'resolve' in request.POST:
            if hasattr(request.user, 'profile') and request.user.profile.is_staff_member():
                ticket.status = 'resolved'
                ticket.save()
                messages.success(request, f'Ticket #{ticket.id} marked as resolved.')
                # Optional: create a system comment
                Comment.objects.create(ticket=ticket, user=request.user, content='Ticket marked as resolved by staff.')
            else:
                messages.error(request, 'Only staff can resolve tickets.')

        elif 'close' in request.POST:
            if hasattr(request.user, 'profile') and request.user.profile.is_staff_member():
                ticket.status = 'closed'
                ticket.save()
                messages.success(request, f'Ticket #{ticket.id} closed successfully.')
                Comment.objects.create(ticket=ticket, user=request.user, content='Ticket closed by staff.')
            else:
                messages.error(request, 'Only staff can close tickets.')

        elif 'assign_staff' in request.POST:
            if hasattr(request.user, 'profile') and request.user.profile.is_staff_member():
                staff_id = request.POST.get('assigned_to')
                if staff_id:
                    assigned_user = User.objects.filter(id=staff_id, is_staff=True).first()
                    if assigned_user:
                        ticket.assigned_to = assigned_user
                        ticket.save()
                        
                        Notification.objects.create(
                            user=assigned_user,
                            ticket=ticket,
                            # notification_type='assigned',
                            message=f"You have been assigned to ticket #{ticket.id} by {request.user.get_full_name() or request.user.username}."
                        )

                        messages.success(request, f'Ticket #{ticket.id} assigned to {assigned_user.username}.')
                        Comment.objects.create(ticket=ticket, user=request.user, content=f'Ticket assigned to {assigned_user.username}.')
                    else:
                        messages.error(request, 'Invalid staff selected.')
                else:
                    messages.error(request, 'No staff member selected.')
            else:
                messages.error(request, 'Only staff can assign tickets.')
        elif "reopen" in request.POST:
            ticket.status = "open"
            ticket.save()

            # Add auto activity log
            Comment.objects.create(
                ticket=ticket,
                user=request.user,
                content="Ticket reopened.",
                is_internal=False
            )

            messages.success(request, "Ticket has been reopened successfully.")
            return redirect("tickets:ticket_detail", ticket.id)
        return redirect('tickets:ticket_detail', ticket_id=ticket.id)

    comments = ticket.comments.all()
    if not (hasattr(request.user, 'profile') and request.user.profile.is_staff_member()):
        comments = comments.filter(is_internal=False)
        # ticket._filtered_comments = ticket.comments.filter(is_internal=False)
    # else:
    #     ticket._filtered_comments = ticket.comments.all()
    
    
    return render(request, 'tickets/ticket_detail.html', {
        'ticket': ticket,
        'comments': comments,
        'staff_list': staff_list
    })
    

@login_required
def add_comment(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        is_internal = request.POST.get('is_internal') == 'on'
        
        if not content.strip():
            messages.error(request, 'Comment cannot be empty.')
            return redirect('tickets:ticket_detail', ticket_id=ticket_id)

        if content:
            ticket.add_comment(request.user, content, is_internal)
            print(Comment.objects.filter(ticket=ticket).count())
            messages.success(request, 'Comment added.')
            # Comment.objects.create(
            #     ticket=ticket,
            #     user=request.user,
            #     content=content,
            #     is_internal=is_internal
            # )
            
            # if ticket.created_by != request.user:
            #     Notification.objects.create(
            #         user=ticket.created_by,
            #         ticket=ticket,
            #         message=f"New comment on ticket #{ticket.id}"
            #     )
            
            # messages.success(request, 'Comment added.')
    
    return redirect('tickets:ticket_detail', ticket_id=ticket_id)

@login_required
def notifications(request):
    notifications = request.user.notifications.order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    today_count = notifications.filter(created_at__date=date.today()).count()
    if request.method == 'POST':
        # Mark all read
        if 'mark_all_read' in request.POST:
            notifications.filter(is_read=False).update(is_read=True)
            messages.success(request, "All notifications marked as read.")
        elif 'delete_all' in request.POST:
            notifications.delete()
            messages.success(request, "All notifications cleared.")
        elif 'mark_read' in request.POST:
            notif_id = request.POST.get('notification_id')
            Notification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
        elif 'delete' in request.POST:
            notif_id = request.POST.get('notification_id')
            Notification.objects.filter(id=notif_id, user=request.user).delete()

        return redirect('tickets:notifications')

    return render(request, 'tickets/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
        'today_count': today_count,
    })

@login_required
def mark_notification_read(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.is_read = True
    notif.save()

    # ✅ Allow redirect to 'next' URL if passed from template
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)

    # ✅ Default behavior if no 'next' param provided
    if notif.ticket:
        return redirect('tickets:ticket_detail', pk=notif.ticket.id)
    return redirect('tickets:notifications')
    

@login_required
def edit_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Permission check
    if not (ticket.created_by == request.user or 
            (hasattr(request.user, 'profile') and request.user.profile.is_staff_member())):
        messages.error(request, 'You do not have permission to edit this ticket.')
        return redirect('tickets:ticket_detail', ticket_id=ticket.id)
    
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ticket updated successfully.')
            return redirect('tickets:ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketForm(instance=ticket)
    
    return render(request, 'tickets/edit_ticket.html', {
        'form': form,
        'ticket': ticket
    })
