from django.shortcuts import render, redirect, get_object_or_404
from .models import Event, Ticket
from django.forms import inlineformset_factory
from .forms import RegistrationForm, EventForm, TicketForm, TicketFormSet
from .models import Event, Booking, Ticket
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.db import transaction
from io import BytesIO
from django.core.files import File
from django.contrib import messages
from eventproj.settings import paypalrestsdk
from django.conf import settings

def home(request):
    categories = ['Corporate', 'Wedding', 'Workshop', 'Concert'] 
    
    categorized_events = {
            category: Event.objects.filter(category__name__icontains=category) for category in categories
    }
    return render(request, 'eventapp/home.html', {
        'categorized_events': categorized_events
    })
    
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.user_type == 'attendee': 
                return redirect('attendee_dashboard') 
            elif user.user_type == 'organizer':
                return redirect('organizer_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'eventapp/login.html')

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login') 
    else:
        form = RegistrationForm()
    return render(request, 'eventapp/register.html', {'form': form})

# Organizer Dashboard
@login_required
def organizer_dashboard(request):
    events = Event.objects.filter(organizer=request.user)
    event_data = []

    for event in events:
        bookings = Booking.objects.filter(event=event, is_paid=True)
        refunds = Booking.objects.filter(event=event, is_refunded=True)
        total_tickets = sum([booking.quantity for booking in bookings])
        total_revenue = sum([booking.total_price for booking in bookings]) - sum([refund.total_price for refund in refunds])

        event_data.append({
            'event': event,
            'total_tickets': total_tickets,
            'total_revenue': total_revenue,
            'bookings': bookings,
        })

    return render(request, 'eventapp/organizer_dashboard.html', {
        'event_data': event_data,
    })

@login_required
def create_event(request):
    if request.method == "POST":
        event_form = EventForm(request.POST, request.FILES)
        ticket_formset = TicketFormSet(request.POST, queryset=Ticket.objects.none())
        
        if event_form.is_valid() and ticket_formset.is_valid():
            event = event_form.save(commit=False)
            event.organizer = request.user
            event.save()

            tickets = ticket_formset.save(commit=False)
            for ticket in tickets:
                ticket.event = event  # Link ticket to the event
                ticket.save()
                
            return redirect('organizer_dashboard')
    else:
        event_form = EventForm()
        ticket_formset = TicketFormSet(queryset=Ticket.objects.none())  # No pre-existing tickets

    return render(request, 'eventapp/create_event.html', {
        'event_form': event_form,
        'ticket_formset': ticket_formset,
    })
    
@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    TicketFormSet = inlineformset_factory(
        Event,
        Ticket,
        form=TicketForm,
        extra=0,  
        can_delete=True
    )
    
    if request.method == "POST":
        event_form = EventForm(request.POST, request.FILES, instance=event)
        ticket_formset = TicketFormSet(request.POST, instance=event)

        if event_form.is_valid() and ticket_formset.is_valid():
            event_form.save()
            ticket_instances = ticket_formset.save(commit=False)
            
            # save tickets and handle deletions
            for ticket in ticket_instances:
                ticket.event = event  
                ticket.save()
                
            for deleted_ticket in ticket_formset.deleted_objects:
                deleted_ticket.delete()
                
            return redirect('organizer_dashboard')
    else:
        event_form = EventForm(instance=event)
        ticket_formset = TicketFormSet(instance=event)

    return render(request, 'eventapp/edit_event.html', {
        'event_form': event_form,
        'ticket_formset': ticket_formset,
        'event': event,
    })

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    if request.method == "POST":
        event.delete()
        messages.success(request, "Event deleted successfully.")
        return redirect('organizer_dashboard')
    return render(request, 'eventapp/delete_event.html', {'event': event})

@login_required
def view_attendees(request, event_id):
    event = Event.objects.get(id=event_id)
    bookings = Booking.objects.filter(event=event)
    total_revenue = sum([booking.price for booking in bookings])
    
    return render(request, 'eventapp/view_attendees.html', {
        'event': event,
        'bookings': bookings,
        'total_revenue': total_revenue,
    })

def event_details(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    # Fetch all tickets related to the event
    tickets = Ticket.objects.filter(event=event, tickets_available__gt=0)
    return render(request, 'eventapp/event_details.html', {'event': event, 'tickets': tickets})

# Attendee Dashboard
@login_required
def attendee_dashboard(request):
    user = request.user

    all_events = Event.objects.all()
    
    booked_tickets = Ticket.objects.select_related('event').filter(attendee=request.user).exclude(refunded=True)
    print(booked_tickets)
    attendees_info = None
    if user.user_type == 'organizer':  
        attendees_info = Ticket.objects.select_related('attendee', 'event')

    context = {
        'booked_tickets': booked_tickets,  
        'all_events': all_events,        
        'calendar_events': all_events,    
        'attendees_info': attendees_info,  
    }

    return render(request, 'eventapp/attendee_dashboard.html', context)

@login_required
def buy_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.method == "POST":
        ticket_type = request.POST['ticket_type']
        quantity = int(request.POST['quantity'])
        
        if quantity > ticket.tickets_available:
            messages.error(request, "Not enough tickets available.")
            return redirect('eventapp:event_details', event_id=ticket.event.id)
        
        price_per_ticket = (
            ticket.price_early_bird if ticket_type == "early_bird" else
            ticket.price_general if ticket_type == "general" else
            ticket.price_vip
        )
        total_price = price_per_ticket * quantity

        # Atomic transaction to ensure data consistency
        with transaction.atomic():
            # Reduce available tickets
            ticket.tickets_available -= quantity
            ticket.save()

            # Create a single "batch" entry for the purchase
            purchased_batch = Ticket.objects.create(
                event=ticket.event,
                attendee=request.user,
                ticket_type=ticket_type,
                quantity=quantity,
                tickets_available=0,  
                price_early_bird=ticket.price_early_bird,
                price_general=ticket.price_general,
                price_vip=ticket.price_vip,
            )
            
            # Create a booking entry for payment tracking
            booking = Booking.objects.create(
                event=ticket.event,
                attendee=request.user,
                ticket_type=ticket_type,
                quantity=quantity,
                total_price=total_price,
                is_paid=False,
            )
        
        messages.success(request, f"Booking #{booking.id} successfully created!")
        return redirect('payment_gateway', booking_id=booking.id)
    
    return render(request, 'eventapp/buy_ticket.html', {'ticket': ticket})

@login_required
def refund_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, attendee=request.user)

    if ticket.refunded:
        messages.error(request, "This ticket has already been refunded.")
        return redirect('attendee_dashboard')

    # Find the original event ticket record (e.g., the one with tickets_available tracking)
    # Ensure you identify this correctly, e.g., by using the ticket type
    original_event_ticket = Ticket.objects.filter(
        event=ticket.event, 
        ticket_type=ticket.ticket_type
    ).first()  # Use .first() to safely get the first matching ticket

    if not original_event_ticket:
        messages.error(request, "Original event ticket record not found.")
        return redirect('attendee_dashboard')

    # Add the refunded ticket quantity back to available tickets
    original_event_ticket.tickets_available += ticket.quantity
    original_event_ticket.save()

    # Mark the user's ticket as refunded
    ticket.refunded = True
    ticket.save()

    # Notify the user
    messages.success(request, "Your refund request has been processed.")
    return redirect('attendee_dashboard')

@login_required
def payment_gateway(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, attendee=request.user)
    return render(request, 'eventapp/payment_gateway.html', {'booking': booking})

@login_required
def confirm_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, attendee=request.user)
    if request.method == "POST":
        # Create PayPal payment
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": request.build_absolute_uri('/payment/success/'),
                "cancel_url": request.build_absolute_uri('/payment/cancel/')
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": booking.event.title,
                        "sku": booking.ticket_type,
                        "price": str(booking.total_price),
                        "currency": "USD",
                        "quantity": booking.quantity
                    }]
                },
                "amount": {
                    "total": str(booking.total_price),
                    "currency": "USD"
                },
                "description": f"Payment for {booking.event.title} tickets."
            }]
        })

        if payment.create():
            # Redirect the user to PayPal for approval
            for link in payment.links:
                if link.rel == "approval_url":
                    return redirect(link.href)
        else:
            messages.error(request, "An error occurred while creating the payment.")
            return redirect('payment_gateway', booking_id=booking_id)

    return redirect('payment_gateway', booking_id=booking_id)

        ## Old logic, doesnt use paypal
        # # Mark booking as confirmed
        # booking.is_paid = True
        # booking.save()

        # # Update ticket count
        # event = booking.event
        # ticket = Ticket.objects.filter(
        #     event=event, ticket_type=booking.ticket_type
        # ).first()
        # if ticket:
        #     ticket.tickets_available -= booking.quantity
        #     ticket.save()
            
        # messages.success(request, "Payment successful! Your tickets have been booked.")
        # return redirect('attendee_dashboard')
    # return redirect('payment_gateway', booking_id=booking_id)

@login_required
def process_refund(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, attendee=request.user, is_paid=True)

    if request.method == "POST":
        # Mark booking as refunded
        booking.is_paid = False
        booking.save()

        # Restore ticket availability
        ticket = Ticket.objects.filter(
            event=booking.event, ticket_type=booking.ticket_type
        ).first()
        if ticket:
            ticket.tickets_available += booking.quantity
            ticket.save()

        # Notify user
        messages.success(request, f"Your refund for {booking.event.title} has been processed.")
        return redirect('attendee_dashboard')

    return redirect('attendee_dashboard')

@login_required
def payment_success(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    payment = paypalrestsdk.Payment.find(payment_id)
    if payment.execute({"payer_id": payer_id}):
        # Mark the booking as paid
        booking_id = request.session.get('booking_id')
        booking = get_object_or_404(Booking, id=booking_id, attendee=request.user)
        booking.is_paid = True
        booking.save()

        # Update ticket count
        ticket = Ticket.objects.filter(
            event=booking.event, ticket_type=booking.ticket_type
        ).first()
        if ticket:
            ticket.tickets_available -= booking.quantity
            ticket.save()

        messages.success(request, "Payment successful! Your tickets have been booked.")
        return redirect('attendee_dashboard')
    else:
        messages.error(request, "Payment execution failed.")
        return redirect('payment_gateway', booking_id=request.session.get('booking_id'))
    
def payment_cancel(request):
    messages.warning(request, "Payment was canceled.")
    return redirect('attendee_dashboard')
