from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import qrcode
from io import BytesIO
from django.core.files import File

class CustomUser(AbstractUser):
    user_type = models.CharField(
        max_length=20, 
        choices=[('attendee', 'Attendee'), ('organizer', 'Organizer')]
    )

class EventCategory(models.Model):
    CATEGORY_CHOICES = [
        ('corporate', 'Corporate Conference'),
        ('wedding', 'Wedding'),
        ('concert', 'Concert'),
        ('workshop', 'Workshop'),
    ]
    name = models.CharField(max_length=100, choices=CATEGORY_CHOICES, unique=True)
    
    def __str__(self):
        return self.name
    
class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='organized_events')
    category = models.ForeignKey(EventCategory, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='event_images/')

    def __str__(self):
        return self.name

class Ticket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    attendee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,related_name="tickets")
    ticket_type = models.CharField(max_length=20)
    quantity = models.PositiveIntegerField(default=1)
    tickets_available = models.IntegerField(default=0)
    price_early_bird=models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_general = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_vip = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    qr_code = models.ImageField(upload_to='qr_codes', blank=True, null=True)
    refunded = models.BooleanField(default=False)  
    
    def save(self, *args, **kwargs):
        if self.attendee and not self.refunded:  # Don't generate QR code for refunded tickets
            qr = qrcode.QRCode(
                version=1,
                box_size=10,
                border=5
            )
            qr_data = (
                f"Event: {self.event.title}, "
                f"Type: {self.ticket_type}, "
                f"Quantity: {self.quantity}, "
                f"Attendee: {self.attendee.username}"
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')

            buffer = BytesIO()
            img.save(buffer, format='PNG')
            self.qr_code.save(f"{self.event.title}_{self.attendee.username}.png", File(buffer), save=False)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ticket for {self.event.title} by {self.attendee.username if self.attendee else 'None'}"
    
class Booking(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    attendee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    ticket_type = models.CharField(max_length=100)
    quantity = models.IntegerField(default=1) 
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Default price to 0.00
    booking_date = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    is_refunded = models.BooleanField(default=False)
    
    def __str__(self):
        return f'{self.attendee.username} - {self.event.title}'

class Profile(models.Model):
    ROLE_CHOICES = [
        ('attendee', 'Attendee'),
        ('organizer', 'Organizer'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='attendee')

    def __str__(self):
        return self.user.username

