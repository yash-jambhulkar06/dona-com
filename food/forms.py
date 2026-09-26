from datetime import datetime, date
from django import forms
from django.utils import timezone
from .models import FreeFoodEvent, Report, FoodRescueClaim

class FreeFoodEventForm(forms.ModelForm):
    """Form for authenticated community members to submit free-food events."""
    class Meta:
        model = FreeFoodEvent
        fields = [
            'title',
            'event_type',
            'dietary_type',
            'allergens_info',
            'food_details',
            'description',
            'event_date',
            'start_time',
            'end_time',
            'venue_name',
            'address',
            'latitude',
            'longitude',
            'is_surplus_food',
            'surplus_quantity',
            'rescue_contact_phone',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Mahaprasad at ISKCON Temple'}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'dietary_type': forms.Select(attrs={'class': 'form-select'}),
            'allergens_info': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Nut-Free, Gluten-Free, Dairy-Free options'}),
            'food_details': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'e.g. Pure Veg Thali (Dal, Rice, Roti, Sabzi, Kheer). Clean drinking water available.'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'e.g. Open to everyone. Organized on the occasion of temple anniversary.'}),
            'event_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'venue_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Community Hall / Temple Compound'}),
            'address': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Complete street address, landmarks'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-input coord-input', 'step': '0.0000001', 'readonly': 'readonly'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-input coord-input', 'step': '0.0000001', 'readonly': 'readonly'}),
            'is_surplus_food': forms.CheckboxInput(attrs={'class': 'form-checkbox', 'id': 'id_is_surplus_food'}),
            'surplus_quantity': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 50+ meals, 3 large vessels'}),
            'rescue_contact_phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. +91 9876543210'}),
        }

    def clean_event_date(self):
        event_date = self.cleaned_data.get('event_date')
        if event_date and event_date < timezone.localtime().date():
            raise forms.ValidationError("Event date cannot be in the past.")
        return event_date

    def clean(self):
        cleaned_data = super().clean()
        event_date = cleaned_data.get('event_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        lat = cleaned_data.get('latitude')
        lng = cleaned_data.get('longitude')
        is_surplus = cleaned_data.get('is_surplus_food')
        rescue_phone = cleaned_data.get('rescue_contact_phone')

        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', "End time must be later than start time.")

        if event_date == timezone.localtime().date() and end_time:
            if end_time < timezone.localtime().time():
                self.add_error('end_time', "Event end time has already passed for today.")

        if lat is not None and not (-90 <= lat <= 90):
            self.add_error('latitude', "Latitude must be between -90 and 90 degrees.")

        if lng is not None and not (-180 <= lng <= 180):
            self.add_error('longitude', "Longitude must be between -180 and 180 degrees.")

        if is_surplus and not rescue_phone:
            self.add_error('rescue_contact_phone', "Please provide a direct phone number for surplus food rescue pickup.")

        return cleaned_data


class ReportForm(forms.ModelForm):
    """Form to submit an issue or report on a listing."""
    class Meta:
        model = Report
        fields = ['reason', 'details']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'details': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Explain what is incorrect or why this listing should be reviewed'}),
        }


class FoodRescueClaimForm(forms.ModelForm):
    """Form for volunteer food rescue networks to claim a surplus food pickup."""
    class Meta:
        model = FoodRescueClaim
        fields = ['volunteer_name', 'volunteer_phone', 'organization', 'estimated_pickup_time', 'notes']
        widgets = {
            'volunteer_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full Name'}),
            'volunteer_phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Mobile Number'}),
            'organization': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Robin Hood Army / Roti Bank / Volunteer Team'}),
            'estimated_pickup_time': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Within 30 mins / 4:00 PM'}),
            'notes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2, 'placeholder': 'Vehicle type, food container capacity, or pickup instructions'}),
        }
