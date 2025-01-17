from datetime import timedelta
from django.utils import timezone
import os
from django import forms
from .models import Appointment, Master, MasterSchedule, Material, Order, OrderAdditionalService, Sale, Schedule, Seller, Service, SoldProduct, SuppliedMaterial, Supply, User, Product, Client, Workshop
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.forms import Select, DateTimeInput, NumberInput, inlineformset_factory, modelformset_factory
from django.core.files.storage import default_storage

User = get_user_model()

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='Email', max_length=254)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise forms.ValidationError('Пользователь с таким email не найден.')

            if not user.check_password(password):
                raise forms.ValidationError('Неверный пароль.')
            
            self.user_cache = user
        return self.cleaned_data
    def get_user(self):
         return self.user_cache
    
class ClientCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Повторите пароль:')
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Дата рождения:')

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Электронная почта',
            'phone_number': 'Номер телефона',
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise forms.ValidationError("Имя не может быть пустым.")
        if not first_name.isalpha():
            raise forms.ValidationError("Имя должно содержать только буквы.")
        return first_name
        
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
             raise forms.ValidationError("Фамилия не может быть пустой.")
        if not last_name.isalpha():
            raise forms.ValidationError("Фамилия должна содержать только буквы.")
        return last_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise forms.ValidationError("Номер телефона не может быть пустым.")
        if not phone_number.isdigit():
              raise forms.ValidationError("Номер телефона должен содержать только цифры.")
        if len(phone_number) < 7 or len(phone_number) > 15:
             raise forms.ValidationError("Номер телефона должен быть от 7 до 15 символов.")
        return phone_number

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password != password2:
            raise forms.ValidationError('Пароли не совпадают')
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
             raise forms.ValidationError("Электронная почта не может быть пустой.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Эта электронная почта уже занята.")
        return email

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if not birth_date:
             raise forms.ValidationError("Дата рождения не может быть пустой.")
        today = timezone.now().date()
        age = (today - birth_date).days // 365
        if age < 14:
            raise forms.ValidationError("Возраст клиента должен быть не менее 14 лет.")
        return birth_date

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_employee = False
        if commit:
            user.save()
            Client.objects.create(user=user, birth_date=self.cleaned_data['birth_date'])
        return user

class MasterCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Повторите пароль')
    experience_since = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Опыт работы с')

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Электронная почта',
            'phone_number': 'Номер телефона',
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise forms.ValidationError("Имя не может быть пустым.")
        if not first_name.isalpha():
            raise forms.ValidationError("Имя должно содержать только буквы.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
            raise forms.ValidationError("Фамилия не может быть пустой.")
        if not last_name.isalpha():
            raise forms.ValidationError("Фамилия должна содержать только буквы.")
        return last_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise forms.ValidationError("Номер телефона не может быть пустым.")
        if not phone_number.isdigit():
            raise forms.ValidationError("Номер телефона должен содержать только цифры.")
        if len(phone_number) < 7 or len(phone_number) > 15:
            raise forms.ValidationError("Номер телефона должен быть от 7 до 15 символов.")
        return phone_number

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password != password2:
            raise forms.ValidationError('Пароли не совпадают')
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Электронная почта не может быть пустой.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Этот email уже используется.")
        return email

    def clean_experience_since(self):
        experience_since = self.cleaned_data.get('experience_since')
        if not experience_since:
            raise forms.ValidationError("Дата начала опыта работы не может быть пустой.")
        if experience_since > timezone.now().date():
             raise forms.ValidationError("Дата начала опыта работы не может быть в будущем.")
        return experience_since

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_employee = True
        if commit:
            user.save()
            Master.objects.create(user=user, experience_since=self.cleaned_data['experience_since'], photo="images/masters/no_photo.png")
        return user


class SellerCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Повторите пароль')

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Электронная почта',
            'phone_number': 'Номер телефона',
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise forms.ValidationError("Имя не может быть пустым.")
        if not first_name.isalpha():
            raise forms.ValidationError("Имя должно содержать только буквы.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
             raise forms.ValidationError("Фамилия не может быть пустой.")
        if not last_name.isalpha():
            raise forms.ValidationError("Фамилия должна содержать только буквы.")
        return last_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise forms.ValidationError("Номер телефона не может быть пустым.")
        if not phone_number.isdigit():
              raise forms.ValidationError("Номер телефона должен содержать только цифры.")
        if len(phone_number) < 7 or len(phone_number) > 15:
             raise forms.ValidationError("Номер телефона должен быть от 7 до 15 символов.")
        return phone_number

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password != password2:
            raise forms.ValidationError('Пароли не совпадают')
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Электронная почта не может быть пустой.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Этот email уже используется.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_employee = True
        if commit:
            user.save()
            Seller.objects.create(user=user)
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'phone_number': 'Номер телефона',
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise forms.ValidationError("Имя не может быть пустым.")
        if not first_name.isalpha():
            raise forms.ValidationError("Имя должно содержать только буквы.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
            raise forms.ValidationError("Фамилия не может быть пустой.")
        if not last_name.isalpha():
            raise forms.ValidationError("Фамилия должна содержать только буквы.")
        return last_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise forms.ValidationError("Номер телефона не может быть пустым.")
        if not phone_number.isdigit():
            raise forms.ValidationError("Номер телефона должен содержать только цифры.")
        if len(phone_number) < 7 or len(phone_number) > 15:
            raise forms.ValidationError("Номер телефона должен быть от 7 до 15 символов.")
        return phone_number

class ClientUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'phone_number': 'Номер телефона',
        }
    birth_date = forms.DateField(label='Дата рождения', widget=forms.DateInput(attrs={'type':'date'}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'client'):
            self.fields['birth_date'].initial = self.instance.client.birth_date

    def clean_first_name(self):
       first_name = self.cleaned_data.get('first_name')
       if not first_name:
           raise forms.ValidationError("Имя не может быть пустым.")
       if not first_name.isalpha():
           raise forms.ValidationError("Имя должно содержать только буквы.")
       return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
             raise forms.ValidationError("Фамилия не может быть пустой.")
        if not last_name.isalpha():
            raise forms.ValidationError("Фамилия должна содержать только буквы.")
        return last_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise forms.ValidationError("Номер телефона не может быть пустым.")
        if not phone_number.isdigit():
            raise forms.ValidationError("Номер телефона должен содержать только цифры.")
        if len(phone_number) < 7 or len(phone_number) > 15:
             raise forms.ValidationError("Номер телефона должен быть от 7 до 15 символов.")
        return phone_number

    def clean_birth_date(self):
      birth_date = self.cleaned_data.get('birth_date')
      if birth_date:
         today = timezone.now().date()
         age = (today - birth_date).days // 365
         if age < 14:
            raise forms.ValidationError("Возраст клиента должен быть не менее 14 лет.")
      return birth_date

    def save(self, commit=True):
      user = super().save(commit)
      if commit and hasattr(user,'client'):
         client = user.client
         birth_date = self.cleaned_data.get('birth_date', None)
         client.birth_date = birth_date
         client.save()
      return user

class MasterUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'phone_number': 'Номер телефона',
        }
    photo = forms.FileField(label='Фото', required=False)
    experience_since = forms.DateField(label='Опыт работы с ',widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'master'):
            initial_photo = getattr(self.instance.master, 'photo', "no_photo.png")
            self.initial['photo'] = initial_photo # Для того, чтобы форма понимала, какое фото выбрать

    def clean_first_name(self):
       first_name = self.cleaned_data.get('first_name')
       if not first_name:
           raise forms.ValidationError("Имя не может быть пустым.")
       if not first_name.isalpha():
           raise forms.ValidationError("Имя должно содержать только буквы.")
       return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
             raise forms.ValidationError("Фамилия не может быть пустой.")
        if not last_name.isalpha():
            raise forms.ValidationError("Фамилия должна содержать только буквы.")
        return last_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise forms.ValidationError("Номер телефона не может быть пустым.")
        if not phone_number.isdigit():
            raise forms.ValidationError("Номер телефона должен содержать только цифры.")
        if len(phone_number) < 7 or len(phone_number) > 15:
             raise forms.ValidationError("Номер телефона должен быть от 7 до 15 символов.")
        return phone_number

    def clean_experience_since(self):
        experience_since = self.cleaned_data.get('experience_since')
        if experience_since:
          if experience_since > timezone.now().date():
             raise forms.ValidationError("Дата начала опыта работы не может быть в будущем.")
        return experience_since

    def save(self, commit=True):
      user = super().save(commit)
      if commit and hasattr(user,'master'):
        master = user.master
        experience_since = self.cleaned_data.get('experience_since', None)
        master.experience_since = experience_since


        if self.cleaned_data['photo']:
           photo = self.cleaned_data['photo']
           filename = default_storage.save(os.path.join('images/masters/', photo.name), photo)
           master.photo = filename  # Сохраняем относительный путь для БД.
        master.save()

      return user

class SellerUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'phone_number': 'Номер телефона',
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise forms.ValidationError("Имя не может быть пустым.")
        if not first_name.isalpha():
            raise forms.ValidationError("Имя должно содержать только буквы.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
            raise forms.ValidationError("Фамилия не может быть пустой.")
        if not last_name.isalpha():
            raise forms.ValidationError("Фамилия должна содержать только буквы.")
        return last_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise forms.ValidationError("Номер телефона не может быть пустым.")
        if not phone_number.isdigit():
             raise forms.ValidationError("Номер телефона должен содержать только цифры.")
        if len(phone_number) < 7 or len(phone_number) > 15:
             raise forms.ValidationError("Номер телефона должен быть от 7 до 15 символов.")
        return phone_number

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['start_time', 'duration']
        labels = {
            'duration': 'Длительность',
            'start_time': 'Время начала смены'
        }
        widgets = {
            'start_time': DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_start_time(self):
        start_time = self.cleaned_data.get('start_time')
        if not start_time:
             raise forms.ValidationError("Время начала смены не может быть пустым.")
        if start_time < timezone.now():
          raise forms.ValidationError("Время начала смены не может быть в прошлом.")
        return start_time

    def clean_duration(self):
        duration = self.cleaned_data.get('duration')
        if not duration:
            raise forms.ValidationError("Длительность не может быть пустой.")
        if duration <= 0:
            raise forms.ValidationError("Длительность должна быть больше нуля.")
        return duration

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance

class ProductForm(forms.ModelForm):
    image = forms.ChoiceField(choices=[], required=False)

    class Meta:
        model = Product
        fields = ('image', 'name', 'price', 'description', 'current_quantity')
        labels = {
            'image': 'Фото',
            'name': 'Название',
            'price': 'Цена',
            'description': 'Описание',
            'current_quantity': 'Остаток на складе',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        image_dir = 'static/images/products/'
        choices = []
        choices.extend(
            (filename, filename) for filename in os.listdir(image_dir) if filename.endswith(('jpg', 'jpeg', 'png', 'gif'))
        )
        self.fields['image'].choices = choices
        self.fields['image'].initial = "no_photo.png"

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Название не может быть пустым.")
        return name

    def clean_price(self):
       price = self.cleaned_data.get('price')
       if not price:
             raise forms.ValidationError("Цена не может быть пустой.")
       if price <= 0:
           raise forms.ValidationError("Цена должна быть больше нуля.")
       return price

    def clean_current_quantity(self):
      current_quantity = self.cleaned_data.get('current_quantity')
      if not current_quantity:
          raise forms.ValidationError("Остаток на складе не может быть пустым.")
      if current_quantity < 0:
        raise forms.ValidationError("Остаток на складе не может быть меньше нуля.")
      return current_quantity

class ServiceForm(forms.ModelForm):
    image = forms.ChoiceField(choices=[], required=False)

    class Meta:
        model = Service
        fields = ('image', 'name', 'price', 'description', 'duration')
        labels = {
            'image': 'Фото',
            'name': 'Название',
            'price': 'Цена',
            'description': 'Описание',
            'duration': 'Длительность',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        image_dir = 'static/images/services/'
        self.fields['image'].choices = [
            (filename, filename) for filename in os.listdir(image_dir) if filename.endswith(('jpg', 'jpeg', 'png', 'gif'))
        ]

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Название не может быть пустым.")
        return name

    def clean_price(self):
       price = self.cleaned_data.get('price')
       if not price:
             raise forms.ValidationError("Цена не может быть пустой.")
       if price <= 0:
           raise forms.ValidationError("Цена должна быть больше нуля.")
       return price

    def clean_duration(self):
        duration = self.cleaned_data.get('duration')
        if not duration:
            raise forms.ValidationError("Длительность не может быть пустой.")
        if duration <= 0:
           raise forms.ValidationError("Длительность должна быть больше нуля.")
        return duration


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ('name', 'price', 'description', 'current_quantity')
        labels = {
            'name': 'Название',
            'price': 'Цена',
            'description': 'Описание',
            'current_quantity': 'Остаток на складе',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Название не может быть пустым.")
        return name

    def clean_price(self):
       price = self.cleaned_data.get('price')
       if not price:
             raise forms.ValidationError("Цена не может быть пустой.")
       if price <= 0:
           raise forms.ValidationError("Цена должна быть больше нуля.")
       return price

    def clean_current_quantity(self):
      current_quantity = self.cleaned_data.get('current_quantity')
      if not current_quantity:
          raise forms.ValidationError("Остаток на складе не может быть пустым.")
      if current_quantity < 0:
        raise forms.ValidationError("Остаток на складе не может быть меньше нуля.")
      return current_quantity

class WorkshopForm(forms.ModelForm):
    image = forms.ChoiceField(choices=[], required=False)

    class Meta:
        model = Workshop
        fields = ('name', 'price', 'description', 'capacity', 'area', 'image')
        labels = {
            'image': 'Фото',
            'name': 'Название',
            'price': 'Цена',
            'description': 'Описание',
            'capacity': 'Вместительность',
            'area': 'Площадь',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        image_dir = 'static/images/workshops'
        self.fields['image'].choices = [
            (filename, filename) for filename in os.listdir(image_dir) if filename.endswith(('jpg', 'jpeg', 'png', 'gif'))
        ]
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Название не может быть пустым.")
        return name

    def clean_price(self):
       price = self.cleaned_data.get('price')
       if not price:
             raise forms.ValidationError("Цена не может быть пустой.")
       if price <= 0:
           raise forms.ValidationError("Цена должна быть больше нуля.")
       return price

    def clean_capacity(self):
      capacity = self.cleaned_data.get('capacity')
      if not capacity:
          raise forms.ValidationError("Вместительность не может быть пустой.")
      if capacity <= 0:
          raise forms.ValidationError("Вместительность должна быть больше нуля.")
      return capacity
    
    def clean_area(self):
      area = self.cleaned_data.get('area')
      if not area:
          raise forms.ValidationError("Площадь не может быть пустой.")
      if area <= 0:
          raise forms.ValidationError("Площадь должна быть больше нуля.")
      return area


class SaleForm(forms.Form):
    client_id = forms.ModelChoiceField(queryset=Client.objects.all(), label="Клиент", widget=Select())
    seller_id = forms.ModelChoiceField(queryset=Seller.objects.all(), label="Продавец", widget=Select())
    purchase_date = forms.DateTimeField(label="Дата и время", widget=DateTimeInput(attrs={'type': 'datetime-local'}), required=False)
    
    product_ids = forms.ModelMultipleChoiceField(queryset=Product.objects.all(), label="Товары", widget=forms.SelectMultiple(), required=False)
    quantities = forms.IntegerField(label="Количество", widget=NumberInput(attrs={'type': 'number'}), initial=1, required=False)

    def __init__(self, *args, **kwargs):
        super(SaleForm, self).__init__(*args, **kwargs)
        self.fields['product_ids'].widget.attrs.update({'class': 'product-select'})
        self.fields['quantities'].widget.attrs.update({'class': 'quantity-input'})
        
    def clean_purchase_date(self):
      purchase_date = self.cleaned_data.get('purchase_date')
      if purchase_date:
        if purchase_date > timezone.now():
            raise forms.ValidationError("Дата покупки не может быть в будущем.")
      return purchase_date

    def clean(self):
      cleaned_data = super().clean()
      product_ids = cleaned_data.get("product_ids")
      quantities = cleaned_data.get("quantities")
      
      if product_ids and not quantities:
        self.add_error('quantities', "Укажите количество товара.")

      if not product_ids and quantities:
          self.add_error('product_ids', "Выберите товар.")
      
      if product_ids and quantities:
          if quantities <= 0:
              self.add_error('quantities', "Количество должно быть больше нуля.")
          
      
      return cleaned_data
      
    def save(self, commit=True):
        client_id = self.cleaned_data['client_id']
        seller_id = self.cleaned_data['seller_id']
        purchase_date = self.cleaned_data['purchase_date']
        sale = Sale(client=client_id, seller=seller_id, purchase_date=purchase_date)
       
        if commit:
          if purchase_date:
            sale.purchase_date = purchase_date
          sale.save()
           
        product_ids = self.cleaned_data.get("product_ids")
        quantities = self.cleaned_data.get("quantities")
    
        if product_ids and quantities: 
          for product_id in product_ids:
             SoldProduct.objects.create(sale=sale, product=product_id, quantity=quantities)

        return sale

class SaleUpdateForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['client', 'seller', 'purchase_date', 'is_paid', 'is_gathered','is_given']
        labels = {
            'client': 'Клиент',
            'seller': 'Продавец',
            'purchase_date': 'Дата и время покупки',
            'is_paid': 'Оплачено',
            'is_gathered': 'Собрано',
            'is_given': 'Выдано',
        }
        
        widgets = {
            'client': Select(),
            'seller': Select(),
            'purchase_date': DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       self.fields['client'].queryset = Client.objects.all()
       self.fields['seller'].queryset = Seller.objects.all()

    def clean_purchase_date(self):
       purchase_date = self.cleaned_data.get('purchase_date')
       if purchase_date:
         if purchase_date > timezone.now():
            raise forms.ValidationError("Дата покупки не может быть в будущем.")
       return purchase_date

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance
    
class SoldProductForm(forms.ModelForm):
    class Meta:
        model = SoldProduct
        fields = ['product', 'quantity']
        labels = {
            'product': 'Товар',
            'quantity': 'Количество',
        }
        widgets = {
            'product': Select(),
            'quantity': NumberInput(attrs={'type': 'number'}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity <= 0:
            raise forms.ValidationError("Количество должно быть больше нуля.")
        return quantity

SoldProductFormSet = modelformset_factory(SoldProduct, form=SoldProductForm, extra=1, can_delete=True)


class DateFilterForm(forms.Form):
    start_date = forms.DateField(label='От', widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    end_date = forms.DateField(label='До', widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Дата 'От' не может быть позже даты 'До'.")
        return cleaned_data


class SupplyForm(forms.ModelForm):
    class Meta:
        model = Supply
        fields = ['seller', 'supply_date']
        labels = {
            'seller': 'Продавец',
            'supply_date': 'Дата и время поставки',
        }
        widgets = {
            'supply_date': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }

    def clean_supply_date(self):
        supply_date = self.cleaned_data['supply_date']
        if supply_date > timezone.now():
            raise forms.ValidationError("Дата поставки не может быть в будущем.")
        return supply_date


class SuppliedMaterialForm(forms.ModelForm):
    class Meta:
        model = SuppliedMaterial
        fields = ['material', 'quantity']
        labels = {
            'material': 'Сырье',
            'quantity': 'Количество',
        }

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity <= 0:
            raise forms.ValidationError("Количество должно быть больше нуля.")
        return quantity

class SupplyMaterialFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        has_errors = any(form.errors for form in self.forms)
        if not self.forms or has_errors:
            return
        materials = [form.cleaned_data['material'] for form in self.forms if form.cleaned_data.get("material")]
        if len(set(materials)) != len(materials):
            raise forms.ValidationError("Нельзя выбрать один и тот же материал несколько раз")


SupplyMaterialFormSet = inlineformset_factory(Supply, SuppliedMaterial,
                                                 form=SuppliedMaterialForm,
                                                 formset=SupplyMaterialFormSet,
                                                 extra=1,
                                                 can_delete=True
                                                 )

class AppointmentOrderForm(forms.Form):
    workshop = forms.ModelChoiceField(queryset=Workshop.objects.all(), label="Мастерская")
    master = forms.ModelChoiceField(queryset=Master.objects.all(), label="Мастер", required=False)
    client = forms.ModelChoiceField(queryset=Client.objects.all(), label="Клиент")
    start_time = forms.DateTimeField(label="Начало", widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    main_service = forms.ModelChoiceField(queryset=Service.objects.all(), label="Основная услуга")

    is_paid = forms.BooleanField(label="Оплачено", required=False, initial=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_start_time(self):
        start_time = self.cleaned_data.get('start_time')
        if start_time < timezone.now():
            raise forms.ValidationError("Дата начала не может быть в прошлом.")
        return start_time

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        main_service = cleaned_data.get('main_service')

        if start_time and main_service:
            if main_service.duration:
                cleaned_data['end_time'] = start_time + timedelta(minutes=main_service.duration)
            else:
                self.add_error('main_service', "У выбранной услуги не задано время.")

        return cleaned_data

    def save(self, commit=True):
        workshop = self.cleaned_data['workshop']
        master = self.cleaned_data['master']
        client = self.cleaned_data['client']
        start_time = self.cleaned_data['start_time']
        end_time = self.cleaned_data['end_time']
        main_service = self.cleaned_data['main_service']
        is_paid = self.cleaned_data['is_paid']

        appointment = Appointment.objects.create(
            workshop=workshop,
            master=master,
            client=client.user,
            start_time=start_time,
            end_time=end_time,
            main_service=main_service
        )

        order = Order.objects.create(
            appointment=appointment,
            is_paid=is_paid
        )

        return order


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['workshop', 'master', 'start_time', 'end_time', 'main_service']
        labels = {
            'workshop': 'Мастерская',
            'master': 'Мастер',
            'start_time': 'Начало',
            'end_time': 'Конец',
            'main_service': 'Основная услуга',
        }
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_start_time(self):
      start_time = self.cleaned_data.get('start_time')
      if start_time < timezone.now():
        raise forms.ValidationError("Время начала приема не может быть в прошлом.")
      return start_time

    def clean(self):
      cleaned_data = super().clean()
      start_time = cleaned_data.get('start_time')
      end_time = cleaned_data.get('end_time')

      if start_time and end_time and start_time >= end_time:
        raise forms.ValidationError("Время начала должно быть раньше времени окончания приема.")
      return cleaned_data


class OrderAdditionalServiceForm(forms.ModelForm):
    class Meta:
        model = OrderAdditionalService
        fields = [
            'order',
            'service'
        ]
        labels = {
            'order': 'Заказ',
            'service': 'Услуга',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class OrderUpdateForm(forms.ModelForm):
    is_paid = forms.BooleanField(label="Оплачено", required=False, initial=False)

    class Meta:
        model = Order
        fields = ['is_paid']
        labels = {
            'is_paid': 'Оплачено',
        }
    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       for field in self.fields.values():
         field.widget.attrs.update({'class': 'form-control'})


OrderAdditionalServiceFormSet = inlineformset_factory(
    Order,
    OrderAdditionalService,
    form=OrderAdditionalServiceForm,
    extra=1,
    can_delete=True
)