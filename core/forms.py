from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
import re
User = get_user_model()

class LoginForm(forms.Form):
    phone = forms.CharField(
        max_length=32, 
        required=True, 
        label='شماره موبایل',
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 
                   'شماره تلفن باید در قالب صحیح وارد شود. حداکثر 15 رقم مجاز است.')]
    )
    password = forms.CharField(
        widget=forms.PasswordInput(render_value=False), 
        required=True, 
        label='رمز عبور'
    )
    remember = forms.BooleanField(required=False, initial=False, label='مرا به خاطر بسپار')

    def clean_phone(self):
        ph = (self.cleaned_data.get('phone') or '').strip()
        if not ph:
            raise forms.ValidationError('شماره موبایل را وارد کنید')
        return ph


class RegisterForm(forms.Form):
    phone = forms.CharField(
        max_length=32, 
        required=True, 
        label='شماره موبایل',
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 
                   'شماره تلفن باید در قالب صحیح وارد شود. .')]
    )
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label='نام'
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label='نام خانوادگی'
    )
    email = forms.EmailField(required=False, label='ایمیل')
    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        max_length=500,
        required=False,
        label='آدرس'
    )
    password = forms.CharField(
        widget=forms.PasswordInput, 
        required=True, 
        label='رمز عبور'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput, 
        required=True, 
        label='تکرار رمز عبور'
    )

    def __init__(self, *args, **kwargs):
        # normalize incoming POST keys so templates that use 'password1' still work
        super().__init__(*args, **kwargs)
        try:
            if hasattr(self, 'data') and self.data:
                data = self.data.copy()
                if 'password1' in data and 'password' not in data:
                    data['password'] = data.get('password1')
                self.data = data
        except Exception:
            pass

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        if not phone:
            raise forms.ValidationError('شماره موبایل را وارد کنید')
        
        # Check if phone number already exists
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError('شماره تلفن وارد شده قبلاً ثبت شده است.')
        
        return phone

    def clean(self):
        data = super().clean()
        p1 = data.get('password')
        p2 = data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('رمزهای عبور مطابقت ندارند')
        # ensure callers can access the password under the key 'password'
        # (views expect form.cleaned_data.get('password'))
        if p1:
            data['password'] = p1
        return data

    def save(self, commit=True):
        phone = self.cleaned_data.get('phone')
        password = self.cleaned_data.get('password')
        email = self.cleaned_data.get('email') or ''
        first_name = self.cleaned_data.get('first_name') or ''
        last_name = self.cleaned_data.get('last_name') or ''
        address = self.cleaned_data.get('address') or ''

        extra = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'address': address
        }
        create_user = getattr(User.objects, 'create_user', None)

        # If caller asked for commit=False, return unsaved instance so caller can set extra attrs
        if not commit:
            user = User(**{'phone': phone, 'email': email, 'first_name': first_name, 'last_name': last_name, 'address': address})
            return user

        # commit=True -> create and save the user (use manager if available)
        if callable(create_user):
            user = create_user(phone=phone, password=password, **extra)
        else:
            user = User(phone=phone, email=email, first_name=first_name, last_name=last_name, address=address)
            user.set_password(password)
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=15, 
        label='شماره موبایل',
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 
                   'شماره تلفن باید در قالب صحیح وارد شود.')],
        disabled=True  # شماره تلفن قابل تغییر نیست
    )
    address = forms.CharField(
        widget=forms.Textarea, 
        required=False, 
        label='آدرس',
        max_length=500,
        help_text='حداکثر 500 کاراکتر مجاز است'
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'language']

class AddressForm(forms.ModelForm):
    """Slim profile form used on the profile page.
    Only allows editing user's public info (not phone/username).
    """
    
    first_name = forms.CharField(
        max_length=150,
        required=False,
        label='نام',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label='نام خانوادگی',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    email = forms.EmailField(
        required=False,
        label='ایمیل',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    address = forms.CharField(
        required=False,
        label='آدرس',
        max_length=500,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'address']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure all fields have proper initial values from the instance
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.first_name or ''
            self.fields['last_name'].initial = self.instance.last_name or ''
            self.fields['email'].initial = self.instance.email or ''
            self.fields['address'].initial = self.instance.address or ''
