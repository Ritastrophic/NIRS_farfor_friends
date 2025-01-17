from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

def create_superuser(email, password):
    """Создает суперпользователя без использования командной строки."""
    User = get_user_model()
    try:
        user = User.objects.get(email=email)
        if user.is_superuser:
           raise Exception(f"Пользователь {email} уже существует и является суперпользователем.")
        else:
           raise Exception(f"Пользователь {email} уже существует и не является суперпользователем")
    except User.DoesNotExist:
        user = User(email=email, is_staff=True, is_superuser=True, first_name='adminka', last_name='adminkovna')
        user.set_password(password)  # Важно использовать set_password для хеширования пароля
        user.save()
        if User.objects.filter(email=email).exists():
           return user
        else:
           raise Exception("Ошибка при создании пользователя.")
    except Exception as e:
        return e