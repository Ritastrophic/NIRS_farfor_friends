from datetime import datetime, timedelta, timezone
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth import get_user_model, logout, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.db.models import Sum, F, Q, Count
from django.db.models.functions import TruncDate
from .forms import AppointmentForm, AppointmentOrderForm, ClientCreationForm, ClientUserUpdateForm, DateFilterForm, EmailAuthenticationForm, MasterCreationForm, MasterUserUpdateForm, MaterialForm, OrderAdditionalServiceFormSet, OrderUpdateForm, ProductForm, SaleForm, SaleUpdateForm, ScheduleForm, SellerCreationForm, SellerUserUpdateForm, ServiceForm, SupplyMaterialFormSet, UserUpdateForm, WorkshopForm, SoldProductFormSet, SupplyForm
from .models import Appointment, Cart, CartItem, Client, Master, MasterSchedule, Material, Order, OrderAdditionalService, Product, Sale, Schedule, Seller, SellerSchedule, Service, SoldProduct, SuppliedMaterial, Supply, Workshop
from .utils import create_superuser
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import json
from django.views.decorators.csrf import csrf_exempt

default_products = [
    ]
default_services = [
    ]



def is_superuser(user):
    return user.is_superuser

def is_seller(user):
    return hasattr(user, 'seller')

def is_client(user):
    return hasattr(user, 'client')

def is_master(user):
  return hasattr(user, 'master') or user.is_superuser

def is_seller_master(user):
    return hasattr(user, 'seller') or hasattr(user, 'master') or user.is_superuser

def is_seller(user):
    return hasattr(user, 'seller') or user.is_superuser

def index(request):
    products = Product.objects.all()
    services = Service.objects.all()
    context = {
        'products': products,
        'services': services
        }
    return render(request, "index.html", context)

def about(request):
    return render(request, "about.html")

def contacts(request):
    return render(request, "contacts.html")


def create_superuser_view(request):
    try:
        user = create_superuser('adminka@example.com', '1234')
        if isinstance(user, get_user_model()):
            return HttpResponse("Суперпользователь создан!")
        else:
            return HttpResponse(f"Ошибка создания: {user}")
    except Exception as e:
        return HttpResponse(f"Ошибка создания: {e}")
    

def auth_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_superuser:
                return redirect('admin_main')
            try:
                user.client
                return redirect('home')
            except:
                pass
            try:
                user.seller
                return redirect('seller_main')
            except:
                pass
            try:
                user.master
                return redirect('master_main')
            except:
                raise Http404
    else:
        form = EmailAuthenticationForm()
    return render(request, 'auth.html', {'form': form})

def client_registration_view(request):
    if request.method == 'POST':
        form = ClientCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ClientCreationForm()
    return render(request, 'personal/client_registration.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home') 


@login_required
def user_personal(request):
    user = request.user
    client, seller, master, role = None, None, None, None

    if user.is_superuser:
        role = 'администратора'
    elif hasattr(user, 'client'):
        client = user.client
        role = 'клиента'
    elif hasattr(user, 'seller'):
        seller = user.seller
        role = 'продавца'
    elif hasattr(user, 'master'):
        master = user.master
        role = 'мастера'
    else:
      raise Http404('Нет такого пользователя')


    context = {
        'user': user,
        'client': client,
        'seller': seller,
        'master': master,
        'role': role
    }

    return render(request, 'personal/user_personal.html', context)

@login_required
def user_update_view(request):
    user = request.user
    form = None

    if request.method == 'POST':
        if user.is_superuser:
            user_form = UserUpdateForm(request.POST, instance=user)
            if user_form.is_valid():
                try:
                    user_form.save()
                    return redirect('user_personal')
                except Exception as e:
                    return HttpResponse(f'Ошибка сохранения: {e}')
        elif hasattr(user, 'client'):
            form = ClientUserUpdateForm(request.POST, instance=user)
        elif hasattr(user, 'seller'):
            form = SellerUserUpdateForm(request.POST, instance=user)
        elif hasattr(user, 'master'):
            form = MasterUserUpdateForm(request.POST, request.FILES, instance=user)
        else:
           return HttpResponse(f'Ошибка')
        
        if form and form.is_valid():
            try:
                form.save()
                return redirect('user_personal')
            except Exception as e:
                return HttpResponse(f'Ошибка сохранения: {e}')

        else:
            user_form = UserUpdateForm(instance=user)
            return render(request, 'clients/client_update.html', {'user_form': user_form, 'form': form, 'user': user})

    else:
        user_form = UserUpdateForm(instance=user)
        if hasattr(user, 'client'):
            form = ClientUserUpdateForm(instance=user)
        elif hasattr(user, 'seller'):
           form = SellerUserUpdateForm(instance=user)
        elif hasattr(user, 'master'):
            form = MasterUserUpdateForm(instance=user)

    return render(request, 'clients/client_update.html', {'form': form, 'user_form': user_form, 'user': user})

@login_required
@user_passes_test(is_client)
def user_delete_view(request):
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        raise Http404('Такого клиента не существует')
    if request.method == 'POST':
        user = client.user
        client.delete()
        user.delete()
        return redirect('home')
    return render(request, 'clients/client_delete.html', {'client': client})

@login_required
@user_passes_test(is_client)
def my_purchases_view(request):
    user = request.user
    sales = Sale.objects.filter(client=user.client).prefetch_related('soldproduct_set__product', 'seller')

    sales_in_progress = sales.filter(is_given=False, is_gathered=False)
    sales_waiting = sales.filter(is_given=False, is_gathered=True)
    sales_given = sales.filter(is_given=True)

    purchases_in_progress_data = []
    purchases_waiting_data = []
    purchases_given_data = []

    def process_sales(sales_data, target_list):
      for sale in sales_data:
          sale_data = {
              'id': sale.id,
              'seller_name': str(sale.seller),
              'purchase_date': sale.purchase_date,
              'sold_products': [],
              'total_sale_price': 0,
          }
          for sold_product in sale.soldproduct_set.all():
              product_data = {
                  'name': sold_product.product.name,
                  'price': sold_product.product.price,
                  'quantity': sold_product.quantity,
                  'product_total': sold_product.product.price * sold_product.quantity,
              }
              sale_data['sold_products'].append(product_data)
              sale_data['total_sale_price'] += product_data['product_total']
          target_list.append(sale_data)

    process_sales(sales_in_progress, purchases_in_progress_data)
    process_sales(sales_waiting, purchases_waiting_data)
    process_sales(sales_given, purchases_given_data)

    context = {
        'purchases_in_progress': purchases_in_progress_data,
        'purchases_waiting': purchases_waiting_data,
        'purchases_given': purchases_given_data,
    }
    return render(request, 'personal/purchases.html', context)

def add_to_cart(request):

    if not request.user.is_authenticated:
        return redirect('products')

    product_id = request.POST.get('product_id')

    product = get_object_or_404(Product, pk=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        cart_item.quantity += 1
        cart_item.save()
    else:
      cart_item.quantity = 1
      cart_item.save()

    return redirect('products')


@login_required
@user_passes_test(is_client)
def update_cart_item(request):
      if request.method == 'POST':
          item_id = request.POST.get('item_id')
          quantity = int(request.POST.get('quantity'))
          
          cart_item = get_object_or_404(CartItem, id=item_id)
          if quantity > 0:
              cart_item.quantity = quantity
              cart_item.save()
          else:
             cart_item.delete() # Если количество меньше 1, то удаляем товар из корзины
          return redirect('user_cart') # Перенаправляем обратно на страницу корзины
      return redirect('user_cart') # Если метод не POST, то тоже редирект

@login_required
@user_passes_test(is_client)
def cart_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    if cart:
        cart_items = cart.items.all()
        total_price = cart.get_total_price()
        return render(request, 'personal/user_cart.html', {'cart_items': cart_items, 'total_price': total_price})
    else:
        return render(request, 'personal/user_cart.html')


def products_view(request):
    products = Product.objects.all()
    return render(request, 'user_views/products.html', {'products': products})

def services_view(request):
    services = Service.objects.all()
    return render(request, 'user_views/services.html', {'services': services})

def workshops_view(request):
    workshops = Workshop.objects.all()
    return render(request, 'user_views/workshops.html', {'workshops': workshops })

def masters_view(request):
    masters = Master.objects.all()
    return render(request, 'user_views/masters.html', {'masters': masters})


def product_detail_view(request, id):
    try:
        data = Product.objects.get(id=id)
    except Product.DoesNotExist:
        raise Http404('Такого товара не существует')
    return render(request, 'user_views/product.html', {'data': data})

def service_detail_view(request, id):
    try:
        data = Product.objects.get(id=id)
    except Product.DoesNotExist:
        raise Http404('Такого товара не существует')
    return render(request, 'user_views/service.html', {'data': data})

def workshop_detail_view(request, id):
    try:
        data = Product.objects.get(id=id)
    except Product.DoesNotExist:
        raise Http404('Такого товара не существует')
    return render(request, 'user_views/workshop.html', {'data': data})

def master_detail_view(request, id):
    try:
        data = Product.objects.get(id=id)
    except Product.DoesNotExist:
        raise Http404('Такого товара не существует')
    return render(request, 'user_views/master.html', {'data': data})


@login_required
@user_passes_test(is_seller)
def clients_list_view(request):
    dataset = Client.objects.all()
    return render(request, "clients/clients.html", {'dataset': dataset})

@login_required
@user_passes_test(is_seller)
def client_create_view(request):
    if request.method == 'POST':
        form = ClientCreationForm(request.POST)
        if form.is_valid():
          form.save()
          return redirect('clients_list')
    else:
        form = ClientCreationForm()
    return render(request, 'clients/client_create.html', {'form': form})

@login_required
@user_passes_test(is_seller)
def client_detail_admin_view(request, id):
    try:
        client = get_object_or_404(Client, id=id)
    except Client.DoesNotExist:
        raise Http404('Такого клиента не существует')
    return render(request, 'clients/client_detail.html', {'client': client})


@login_required
@user_passes_test(is_superuser)
def sellers_list_view(request):
    dataset = Seller.objects.all()
    return render(request, "sellers/sellers.html", {'dataset': dataset})

@login_required
@user_passes_test(is_superuser)
def seller_create_view(request):
    if request.method == 'POST':
        form = SellerCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])
            user.is_employee = True
            user.save()
            Seller.objects.create(user=user)
            return redirect('sellers_list')
    else:
        form = SellerCreationForm()
    return render(request, 'sellers/seller_create.html', {'form': form})

@login_required
@user_passes_test(is_superuser)
def seller_detail_admin_view(request, id):
    try:
        seller = get_object_or_404(Seller, id=id)
    except Seller.DoesNotExist:
        raise Http404('Такого продавца не существует')
    return render(request, 'sellers/seller_detail.html', {'seller': seller})

@login_required
@user_passes_test(is_superuser)
def seller_delete_view(request, pk):
    try:
        seller = Seller.objects.get(pk=pk)
    except Seller.DoesNotExist:
        raise Http404('Такого продавца не существует')
    if request.method == 'POST':
        user = seller.user
        seller.delete()
        user.delete()
        return redirect('sellers_list')
    return render(request, 'sellers/seller_delete.html', {'seller': seller})


@login_required
@user_passes_test(is_superuser)
def masters_list_view(request):
    dataset = Master.objects.all()
    return render(request, "masters/masters.html", {'dataset': dataset})

@login_required
@user_passes_test(is_superuser)
def master_create_view(request):
    if request.method == 'POST':
        form = MasterCreationForm(request.POST)
        if form.is_valid():
           form.save()
           return redirect('masters_list')
    else:
        form = MasterCreationForm()
    return render(request, 'masters/master_create.html', {'form': form})

@login_required
@user_passes_test(is_superuser)
def master_detail_admin_view(request, id):
    try:
        master = get_object_or_404(Master, id=id)
    except Master.DoesNotExist:
        raise Http404('Такого мастера не существует')
    return render(request, 'masters/master_detail.html', {'master': master})

@login_required
@user_passes_test(is_superuser)
def master_delete_view(request, pk):
    try:
        master = Master.objects.get(pk=pk)
    except Master.DoesNotExist:
        raise Http404('Такого мастера не существует')
    if request.method == 'POST':
        user = master.user
        master.delete()
        user.delete()
        return redirect('masters_list')
    return render(request, 'masters/master_delete.html', {'master': master})


@login_required
@user_passes_test(is_seller)
def products_list_view(request):
    name_query = request.GET.get('name_q')
    price_from = request.GET.get('price_from')
    price_to = request.GET.get('price_to')
    quantity_from = request.GET.get('quantity_from')
    quantity_to = request.GET.get('quantity_to')
    products = Product.objects.all()

    if name_query:
        products = products.filter(name__icontains=name_query)

    if price_from:
         try:
            price_from = float(price_from)
            products = products.filter(price__gte=price_from)
         except ValueError:
             pass
    if price_to:
        try:
            price_to = float(price_to)
            products = products.filter(price__lte=price_to)
        except ValueError:
             pass

    if quantity_from:
        try:
            quantity_from = int(quantity_from)
            products = products.filter(current_quantity__gte=quantity_from)
        except ValueError:
              pass
    if quantity_to:
         try:
            quantity_to = int(quantity_to)
            products = products.filter(current_quantity__lte=quantity_to)
         except ValueError:
              pass

    return render(request, 'products/products.html', {'dataset': products,
                                                        'name_q': name_query,
                                                        'price_from': price_from,
                                                         'price_to': price_to,
                                                         'quantity_from': quantity_from,
                                                         'quantity_to': quantity_to})

@login_required
@user_passes_test(is_seller)
def product_create_view(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            image = form.cleaned_data.get('image')
            if image:
                if image == '':  # если выбрано пустое значение
                   product.photo = f'images/products/no_photo.png'
                else:
                   product.photo.name = f'images/products/{image}'
            product.save()
            return redirect('products_list')
    else:
        form = ProductForm()
    return render(request, 'products/product_create.html', {'form': form})

@login_required
@user_passes_test(is_seller)
def product_detail_admin_view(request, id):
    try:
        data = Product.objects.get(id=id)
    except Product.DoesNotExist:
        raise Http404('Такого товара не существует')
    return render(request, 'products/product_detail.html', {'data': data})
    
@login_required
@user_passes_test(is_seller)
def product_update_view(request, id):
    try:
        product  = get_object_or_404(Product, id=id)
    except Exception:
        raise Http404('Такого товара не существует')
    if request.method =='POST':
        form = ProductForm(request.POST, instance=product )
        if form.is_valid():
             image = form.cleaned_data.get('image')
             if image:
                product.photo.name = f'images/products/{image}'
        form.save()
        return redirect('products_list')
    else:
        form = ProductForm(instance = product )
        context ={
            'form':form, 'product ': product 
        }
        return render(request, 'products/product_update.html', context)

@login_required
@user_passes_test(is_seller)
def product_delete_view(request, id):
    try:
        data = get_object_or_404(Product, id=id)
    except Exception:
        raise Http404('Такого товара не существует')
    if request.method == 'POST':
        data.delete()
        return redirect('products_list')
    else:
        return render(request, 'products/product_delete.html')
    

@login_required
@user_passes_test(is_superuser)
def services_list_view(request):
    dataset = Service.objects.all()
    return render(request, "services/services.html", {'dataset': dataset})

@login_required
@user_passes_test(is_superuser)
def service_create_view(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            image = form.cleaned_data.get('image')
            if image:
                service.photo.name = f'images/services/{image}'
            service.save()
            return redirect('services_list')
    else:
        form = ServiceForm()

    return render(request, 'services/service_create.html', {'form': form})

@login_required
@user_passes_test(is_superuser)
def service_detail_admin_view(request, id):
    try:
        data = Service.objects.get(id=id)
    except Service.DoesNotExist:
        raise Http404('Такой услуги не существует')
    return render(request, 'services/service_detail.html', {'data': data})

@login_required
@user_passes_test(is_superuser)
def service_update_view(request, id):
    try:
        service  = get_object_or_404(Service, id=id)
    except Exception:
        raise Http404('Такой услуги не существует')
    if request.method =='POST':
        form = ServiceForm(request.POST, instance=service )
        if form.is_valid():
             image = form.cleaned_data.get('image')
             if image:
                service.photo.name = f'images/services/{image}'
        form.save()
        return redirect('services_list')
    else:
        form = ServiceForm(instance = service )
        context ={
            'form':form, 'service ': service 
        }
        return render(request, 'services/service_update.html', context)

@login_required
@user_passes_test(is_superuser)
def service_delete_view(request, id):
    try:
        data = get_object_or_404(Service, id=id)
    except Exception:
        raise Http404('Такой услуги не существует')
    if request.method == 'POST':
        data.delete()
        return redirect('services_list')
    else:
        return render(request, 'services/service_delete.html')
    

@login_required
@user_passes_test(is_seller)
def materials_list_view(request):
    dataset = Material.objects.all()
    return render(request, "materials/materials.html", {'dataset': dataset})
    
@login_required
@user_passes_test(is_seller)
def material_create_view(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save()
            return redirect('materials_list')  
    else:
        form = MaterialForm()
    return render(request, 'materials/material_create.html', {'form': form})
        
@login_required
@user_passes_test(is_seller)
def material_detail_admin_view(request, id):
    try:
        data = Material.objects.get(id=id)
    except Material.DoesNotExist:
        raise Http404('Такого сырья не существует')
    return render(request, 'materials/material_detail.html', {'data': data})
    
@login_required
@user_passes_test(is_seller)
def material_update_view(request, id):
    try:
        material = get_object_or_404(Material, id=id)
    except Exception:
        raise Http404('Такого сырья не существует')
    if request.method =='POST':
        form = MaterialForm(request.POST, instance=material )
        if form.is_valid():
            form.save()
            return redirect('materials_list')
    else:
        form = MaterialForm(instance = material )
        return render(request, 'materials/material_update.html', {'form': form, 'material': material})
    
@login_required
@user_passes_test(is_seller)
def material_delete_view(request, id):
    try:
        material = get_object_or_404(Material, id=id)
    except Exception:
        raise Http404('Такого сырья не существует')
    if request.method == 'POST':
        material.delete()
        return redirect('materials_list')
    else:
        return render(request, 'materials/material_delete.html', {'material': material})
    

@login_required
@user_passes_test(is_superuser)
def workshops_list_view(request):
    dataset = Workshop.objects.all()
    return render(request, "workshops/workshops.html", {'dataset': dataset})

@login_required
@user_passes_test(is_superuser)
def workshop_create_view(request):
    if request.method == 'POST':
        form = WorkshopForm(request.POST)
        if form.is_valid():
            workshop = form.save(commit=False)
            image = form.cleaned_data.get('image')
            if image:
                workshop.photo.name = f'images/workshops/{image}'
            workshop.save()
            return redirect('workshops_list')
    else:
        form = WorkshopForm()
    return render(request, 'workshops/workshop_create.html', {'form': form})

@login_required
@user_passes_test(is_superuser)
def workshop_detail_admin_view(request, id):
    try:
        data = Workshop.objects.get(id=id)
    except Workshop.DoesNotExist:
        raise Http404('Такой мастерской не существует')
    return render(request, 'workshops/workshop_detail.html', {'data': data})

@login_required
@user_passes_test(is_superuser)
def workshop_update_view(request, id):
    try:
        workshop = get_object_or_404(Workshop, id=id)
    except Exception:
        raise Http404('Такой мастерской не существует')
    if request.method == 'POST':
        form = WorkshopForm(request.POST, instance=workshop)
        if form.is_valid():
            image = form.cleaned_data.get('image')
            if image:
                workshop.photo.name = f'images/workshops/{image}'
            form.save()
            return redirect('workshops_list')
    else:
        form = WorkshopForm(instance=workshop)
        context = {
            'form': form,
            'workshop': workshop
        }
        return render(request, 'workshops/workshop_update.html', context)

@login_required
@user_passes_test(is_superuser)
def workshop_delete_view(request, id):
    try:
        workshop = get_object_or_404(Workshop, id=id)
    except Exception:
        raise Http404('Такой мастерской не существует')
    if request.method == 'POST':
        workshop.delete()
        return redirect('workshops_list')
    else:
        return render(request, 'workshops/workshop_delete.html', {'workshop': workshop})
    
@login_required
@user_passes_test(is_seller)
def sales_list_view(request):
    sales_all = Sale.objects.all().prefetch_related('soldproduct_set__product', 'seller', 'client')

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    seller_id = request.GET.get('seller')
    client_id = request.GET.get('client')
    product_id = request.GET.get('product')
    price_from = request.GET.get('price_from')
    price_to = request.GET.get('price_to')
    status = request.GET.get('status')
    
    q = Q()

    if date_from:
        q &= Q(purchase_date__date__gte=date_from)
    if date_to:
        q &= Q(purchase_date__date__lte=date_to)
    if seller_id:
        q &= Q(seller__id=seller_id)
    if client_id:
        q &= Q(client__id=client_id)
    if product_id:
       q &= Q(soldproduct__product__id=product_id)
    if price_from:
        q &= Q(soldproduct__product__price__gte=price_from)
    if price_to:
        q &= Q(soldproduct__product__price__lte=price_to)

    if status == 'paid':
        q &= Q(is_paid=True)
    if status == 'in_progress':
        q &= Q(is_given=False, is_gathered=False)
    if status == 'waiting':
        q &= Q(is_given=False, is_gathered=True)
    if status == 'given':
        q &= Q(is_given=True)
  
    sales = sales_all.filter(q)
    
    # Вычисляем общую стоимость продаж
    for sale in sales:
       for sold_product in sale.soldproduct_set.all():
          sold_product.product_total_price = sold_product.product.price * sold_product.quantity
       total_sale_price = sum(sold_product.product_total_price for sold_product in sale.soldproduct_set.all())
       sale.total_sale_price = total_sale_price


    sellers = Seller.objects.all()
    clients = Client.objects.all()
    products = Product.objects.all()
    return render(request, 'sales/sales.html', {
        'sales': sales,
        'sellers': sellers,
        'clients': clients,
        'products': products
        })
    

@login_required
@user_passes_test(is_seller)
def sale_create_view(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
             sale = form.save()
             errors = []
             for sold_product in sale.soldproduct_set.all():
                product = sold_product.product
                quantity_sold = sold_product.quantity
                if product.current_quantity < quantity_sold:
                    errors.append(f"Недостаточно товара {product.name} на складе. (Осталось {product.current_quantity} шт.)")

             if errors:
                messages.error(request, "\n".join(errors))
                sale.delete()
                return render(request, 'sales/sale_create.html', {'form': form})
             else:

                for sold_product in sale.soldproduct_set.all():
                     product = sold_product.product
                     product.current_quantity -= sold_product.quantity
                     product.save()

                messages.success(request, "Продажа успешно добавлена!")
                return redirect('sales_list')
        else:
             messages.error(request, "Ошибка добавления продажи, проверьте данные.")
    else:
        form = SaleForm()
    return render(request, 'sales/sale_create.html', {'form': form})

def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    client, _ = Client.objects.get_or_create(user=request.user)
    now = timezone.now()
    current_sellers = Seller.objects.filter(
        sellerschedule__schedule__start_time__lte=now,
        sellerschedule__schedule__end_time__gte=now
    ).order_by('id')
    
    if not current_sellers.exists():
         next_sellers = Seller.objects.filter(
            sellerschedule__schedule__start_time__gt=now
        ).order_by('sellerschedule__schedule__start_time').first()
         seller = next_sellers
    else:
      seller = current_sellers.first()

    if not seller:
         raise Exception("Нет доступных продавцов")

    sale = Sale.objects.create(
        client=client,
        seller=seller,
        is_paid=True,
        purchase_date=timezone.now()
    )

    errors = []
    for cart_item in cart.items.all():
        product = cart_item.product
        quantity_sold = cart_item.quantity
        
        if product.current_quantity < quantity_sold:
            errors.append(f"Недостаточно товара {product.name} на складе. (Осталось {product.current_quantity} шт.)")
    
    if errors:
        sale.delete()
        messages.error(request, "\n".join(errors))
        return redirect('user_cart') # Перенаправление на страницу корзины

    for cart_item in cart.items.all():
        SoldProduct.objects.create(
            sale=sale,
            product=cart_item.product,
            quantity=cart_item.quantity
        )
        product = cart_item.product
        product.current_quantity -= cart_item.quantity
        product.save()
        cart_item.delete()

    cart.delete()
    messages.success(request, "Заказ оформлен успешно!")
    return redirect('products')

@login_required
@user_passes_test(is_seller)
def sale_update_view(request, id):
    sale = get_object_or_404(Sale, id=id)
    sold_products = SoldProduct.objects.filter(sale=sale)
    formset = SoldProductFormSet(queryset=sold_products)
    if request.method == 'POST':
        form = SaleUpdateForm(request.POST, instance=sale)
        formset = SoldProductFormSet(request.POST, queryset=sold_products)
        if form.is_valid() and formset.is_valid():
            form.save()
            instances = formset.save(commit=False)
            for instance in instances:
                instance.sale=sale
                instance.save()
            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, "Продажа успешно изменена!")
            return redirect('sales_list')
        else:
            messages.error(request, "Ошибка изменения продажи, проверьте данные.")
    else:
        form = SaleUpdateForm(instance=sale)
        
    return render(request, 'sales/sale_update.html', {'form': form, 'formset': formset, 'id':id})
    
@login_required
@user_passes_test(is_seller)
def sale_detail_admin_view(request, id):
    sale = get_object_or_404(Sale, id=id)
    sold_products = SoldProduct.objects.filter(sale=sale)
    return render(request, 'sales/sale_detail.html', {'sale': sale, 'sold_products': sold_products})
    
@login_required
@user_passes_test(is_seller)
def sale_delete_view(request, id):
    sale = get_object_or_404(Sale, id=id)
    sale.delete()
    messages.success(request, "Продажа успешно удалена!")
    return redirect('sales_list')


@login_required
@user_passes_test(is_seller)
def supplies_list_view(request):
    date_query = request.GET.get('date_q')
    seller_query = request.GET.get('seller')
    material_query = request.GET.get('material')

    supplies = Supply.objects.all()

    if date_query:
        supplies = supplies.filter(supply_item__purchase_date__date=date_query)


    if seller_query:
        supplies = supplies.filter(supply_item__seller_id=seller_query)


    if material_query:
       supplies = supplies.filter(material_id=material_query)


    # получаем все объекты Seller и Material для отображения в шаблоне
    sellers = Seller.objects.all() # замените Seller на название вашей модели
    materials = Material.objects.all() # замените Material на название вашей модели


    return render(request, 'supplies/supplies.html', {
        'dataset': supplies,
        'date_q': date_query,
        'seller': seller_query,
        'material': material_query,
        'sellers': sellers,
        'materials': materials
    })

@login_required
@user_passes_test(is_seller)
def supply_create_view(request):
    if request.method == 'POST':
        supply_form = SupplyForm(request.POST)
        formset = SupplyMaterialFormSet(request.POST)
        if supply_form.is_valid() and formset.is_valid():
            supply = supply_form.save()
            formset.instance = supply
            formset.save()
            
            # Увеличиваем количество материалов
            for supplied_material in supply.supplied_materials.all():
                material = supplied_material.material
                quantity_supplied = supplied_material.quantity
                material.current_quantity += quantity_supplied
                material.save()
            messages.success(request, "Поставка успешно добавлена!")
            return redirect('supplies_list')
        else:
            messages.error(request, "Ошибка добавления поставки, проверьте данные.")
    else:
        supply_form = SupplyForm()
        formset = SupplyMaterialFormSet(queryset=SuppliedMaterial.objects.none()) # Передайте пустой queryset
    return render(request, 'supplies/supply_create.html', {'supply_form': supply_form, 'formset':formset})

@login_required
@user_passes_test(is_seller)
def supply_detail_admin_view(request, id):
    supply = get_object_or_404(Supply, pk=id)
    formset = SupplyMaterialFormSet(instance=supply)
    return render(request, 'supplies/supply_detail.html', {'supply': supply, 'formset': formset})

@login_required
@user_passes_test(is_seller)
def supply_update_view(request, supply_id):
    supply = get_object_or_404(Supply, id=supply_id)
    if request.method == 'POST':
        supply_form = SupplyForm(request.POST, instance=supply)
        formset = SupplyMaterialFormSet(request.POST, instance=supply)
        if supply_form.is_valid() and formset.is_valid():
            
            # Получаем старые данные перед обновлением
            old_materials = {item.material.id: item.quantity for item in supply.supplied_materials.all()}
            
            supply = supply_form.save()
            formset.save()

            # Обновляем количество материалов
            new_materials = {item.material.id: item.quantity for item in supply.supplied_materials.all()}
            
            for material_id, new_quantity in new_materials.items():
                material = Material.objects.get(id=material_id)
                old_quantity = old_materials.get(material_id, 0) # Получаем старое количество или 0, если материал новый
                
                # Увеличиваем количество
                material.current_quantity += new_quantity - old_quantity
                material.save()
                
            messages.success(request, "Поставка успешно обновлена!")
            return redirect('supplies_list')
        else:
              messages.error(request, "Ошибка обновления поставки, проверьте данные.")
    else:
        supply_form = SupplyForm(instance=supply)
        formset = SupplyMaterialFormSet(instance=supply)
    return render(request, 'supplies/supply_update.html', {'supply_form': supply_form, 'formset': formset})
@login_required
@user_passes_test(is_seller)
def supply_delete_view(request, id):
    supply = get_object_or_404(Supply, pk=id)
    if request.method == 'POST':
        supply.delete()
        return redirect('supplies_list')
    return render(request, 'supplies/supply_delete.html', {'supply': supply})


@login_required
@user_passes_test(is_superuser)
def stats_view(request):
    return render(request, 'statistics/stats.html')

@login_required
@user_passes_test(is_superuser)
def products_stats_view(request):
    top_expensive_products = Product.objects.order_by('-price')[:3] 
    top_cheap_products = Product.objects.order_by('price')[:3] 
    context = {
        'top_expensive_products': top_expensive_products,
        'top_cheap_products': top_cheap_products
    }
    return render(request, 'statistics/products_stats.html', context)

@login_required
@user_passes_test(is_superuser)
def services_stats_view(request):
    top_expensive_services = Service.objects.order_by('-price')[:3] 
    top_cheap_services = Service.objects.order_by('price')[:3] 
    context = {
        'top_expensive_services': top_expensive_services,
        'top_cheap_services': top_cheap_services
    }
    return render(request, 'statistics/services_stats.html', context)

@login_required
@user_passes_test(is_superuser)
def sales_stats_view(request):
    form = DateFilterForm(request.GET)
    start_date = None
    end_date = None

    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')

    sold_products = SoldProduct.objects.all()

    if start_date and end_date:
        sold_products = sold_products.filter(
            sale__purchase_date__date__gte=start_date,
            sale__purchase_date__date__lte=end_date
        )
    elif start_date:
         sold_products = sold_products.filter(
            sale__purchase_date__date__gte=start_date
        )
    elif end_date:
        sold_products = sold_products.filter(
             sale__purchase_date__date__lte=end_date
        )
    total_revenue = sold_products.aggregate(
        total=Sum(F('product__price') * F('quantity')))['total'] or 0

    most_sold_product = sold_products.values(
        'product__name'
    ).annotate(total_quantity=Sum('quantity')).order_by(
        '-total_quantity'
    ).first()

    daily_revenue = sold_products.annotate(
        date=TruncDate('sale__purchase_date')
    ).values('date').annotate(
        total_daily_revenue=Sum(F('product__price') * F('quantity'))
    ).order_by('-total_daily_revenue').first()
    
    context = {
        'total_revenue': total_revenue,
        'most_sold_product': most_sold_product['product__name'] if most_sold_product else None,
        'most_sold_product_quantity': most_sold_product['total_quantity'] if most_sold_product else None,
        'peak_revenue_day': daily_revenue['date'] if daily_revenue else None,
        'peak_revenue_amount': daily_revenue['total_daily_revenue'] if daily_revenue else None,
        'form': form,
    }
    return render(request, 'statistics/sales_stats.html', context)


@login_required
@user_passes_test(is_superuser)
def admin_main(request):
    top_products = Product.objects.annotate(
        order_count=Count('soldproduct')
    ).order_by(F('order_count').desc(), F('price').desc()).all()[:3]
    return render(request, "mains/admin_main.html", {'top_products': top_products})

@login_required
@user_passes_test(is_seller)
def seller_main(request):
    products = Product.objects.all()
    services = Service.objects.all()
    context = {
        'products': products,
        'services': services
        }
    return render(request, "mains/seller_main.html", context)

@login_required
@user_passes_test(is_master)
def master_main(request):
    products = Product.objects.all()
    services = Service.objects.all()
    context = {
        'products': products,
        'services': services
        }
    return render(request, "mains/master_main.html", context)


@login_required
@user_passes_test(is_superuser)
def generate_schedule_for_seller_week():
    print("generate_schedule_for_seller_week is called")
    now = timezone.now()
    start_of_week = now  # Начало недели - текущее время.
    sellers = list(Seller.objects.all())

    if len(sellers) < 2:
        raise Exception("Недостаточно продавцов для формирования графика")

    schedules = []
    days_to_generate = 7  # Генерируем расписание на 7 дней

    # Получаем последние 2 расписания для определения порядка продавцов
    last_schedules = SellerSchedule.objects.order_by('-schedule__start_time')[:2]

    # Определяем порядок продавцов на основе последних расписаний
    if len(last_schedules) == 2:
        seller1 = last_schedules[0].seller
        seller2 = last_schedules[1].seller
        if seller1 == seller2:  # Если совпадают, то берем третьего, пока не будет отличаться
            for schedule in SellerSchedule.objects.order_by('-schedule__start_time')[2:]:
                if schedule.seller != seller1:
                    seller3 = schedule.seller
                    seller1 = seller2
                    seller2 = seller3
                    break
            else:  # Если никого не нашли - то используем третьего продавца из базы
                if len(sellers) > 2:
                    seller1 = sellers[0]
                    seller2 = sellers[2]
                else:
                    seller1 = sellers[0]
                    seller2 = sellers[1]
        else:  # Если не совпадают, берем их в обратном порядке
            pass
    else:  # Если не нашли два расписания - берем первых 2х продавцов из базы
        seller1 = sellers[0]
        seller2 = sellers[1]

    for day in range(days_to_generate):
        date = start_of_week + timedelta(days=day)

        # Проверяем, что день еще не наступил
        if date.date() < now.date():
            continue

        # Продавец 1 (работает 2 дня, затем 2 дня отдыха)
        if day % 4 < 2:
            schedule1_start = timezone.make_aware(
                datetime(
                    date.year,
                    date.month,
                    date.day,
                    10,
                    0,
                    0
                ), timezone.get_default_timezone()
            )

            schedule1_end = timezone.make_aware(
                datetime(
                    date.year,
                    date.month,
                    date.day,
                    20,
                    0,
                    0
                ), timezone.get_default_timezone()
            )

            schedules.append({
                'seller': seller1,
                'start_time': schedule1_start,
                'end_time': schedule1_end,
                'duration': 10,
            })

        # Продавец 2 (работает 2 дня, затем 2 дня отдыха)
        if (day + 2) % 4 < 2:
            schedule2_start = timezone.make_aware(
                datetime(
                    date.year,
                    date.month,
                    date.day,
                    10,
                    0,
                    0
                ), timezone.get_default_timezone()
            )
            schedule2_end = timezone.make_aware(
                datetime(
                    date.year,
                    date.month,
                    date.day,
                    20,
                    0,
                    0
                ), timezone.get_default_timezone()
            )
            schedules.append({
                'seller': seller2,
                'start_time': schedule2_start,
                'end_time': schedule2_end,
                'duration': 10,
            })

    return schedules

@login_required
@user_passes_test(is_superuser)
def create_seller_schedules(request):
    now = timezone.now()
    start_of_week = now - timedelta(days=now.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Удалить существующие расписания на текущую неделю и будущие
    SellerSchedule.objects.filter(schedule__start_time__gte=now.date()).delete()

    try:
      new_schedules = generate_schedule_for_seller_week()
      print("generated")
    except Exception as e:
        messages.error(request, str(e))
        return redirect('seller_schedules')

    for schedule in new_schedules:
        new_schedule = Schedule.objects.create(start_time=schedule['start_time'], end_time=schedule['end_time'],
                                               duration=schedule['duration'])
        SellerSchedule.objects.create(seller=schedule['seller'], schedule=new_schedule)
    messages.success(request, "Расписание успешно создано!")
    return redirect('seller_schedules')

@login_required
@user_passes_test(is_superuser)
def seller_schedules_view(request):
    seller_id = request.GET.get('seller')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    show_past = request.GET.get('show_past')
    q = Q()

    if seller_id:
        q &= Q(seller__id=seller_id)
    if date_from:
        q &= Q(schedule__start_time__date__gte=date_from)
    if date_to:
        q &= Q(schedule__start_time__date__lte=date_to)

    if not show_past:
         q &= Q(schedule__start_time__gte=timezone.now())

    seller_schedules = SellerSchedule.objects.filter(q).order_by('schedule__start_time')
    
    sellers = Seller.objects.all()
    return render(request, 'seller_schedules/seller_schedules.html', {'seller_schedules': seller_schedules, 'sellers': sellers, 'show_past': show_past})

@login_required
@user_passes_test(is_superuser)
def seller_schedule_add_view(request):
    sellers = Seller.objects.all()
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
             schedule = form.save(commit=False)
             schedule.end_time = schedule.start_time + timedelta(hours=schedule.duration)
             schedule.save()
             seller_id = request.POST.get('seller_id')
             seller = get_object_or_404(Seller, pk=seller_id)
             SellerSchedule.objects.create(seller = seller, schedule = schedule)
             messages.success(request, "Расписание успешно добавлено!")
             return redirect('seller_schedules')
    else:
         form = ScheduleForm()
    return render(request, 'seller_schedules/seller_schedule_create.html', {'form': form, 'sellers': sellers})

@login_required
@user_passes_test(is_superuser)
def seller_schedule_detail_view(request, pk):
    seller_schedule = get_object_or_404(SellerSchedule, pk=pk)
    return render(request, 'seller_schedules/seller_schedule_detail.html', {'seller_schedule': seller_schedule})

@login_required
@user_passes_test(is_superuser)
def seller_schedule_update_view(request, pk):
    seller_schedule = get_object_or_404(SellerSchedule, pk=pk)
    if request.method == 'POST':
      form = ScheduleForm(request.POST, instance = seller_schedule.schedule)
      if form.is_valid():
        schedule = form.save(commit=False)
        schedule.end_time = schedule.start_time + timedelta(hours=schedule.duration)
        schedule.save()
        messages.success(request, "Расписание успешно обновлено!")
        return redirect('seller_schedules')
    else:
        form = ScheduleForm(instance = seller_schedule.schedule)
        
    return render(request, 'seller_schedules/seller_schedule_update.html', {'form': form, 'seller_schedule': seller_schedule})

@login_required
@user_passes_test(is_superuser)
def seller_schedule_delete_view(request, pk):
    seller_schedule = get_object_or_404(SellerSchedule, pk=pk)
    if request.method == 'POST':
        seller_schedule.delete()
        messages.success(request, "Расписание успешно удалено!")
        return redirect('seller_schedules')
    return render(request, 'seller_schedules/seller_schedule_delete.html', {'seller_schedule': seller_schedule})


@login_required
@user_passes_test(is_seller)
def my_seller_schedule_view(request):
    try:
        seller = Seller.objects.get(user=request.user)
    except ObjectDoesNotExist:
         return render(request, 'personal/seller_schedule.html', {'seller_schedules': None})
    show_past = request.GET.get('show_past')

    q = Q(seller=seller)
    if not show_past:
        q &= Q(schedule__start_time__gte=timezone.now())
    
    seller_schedules = SellerSchedule.objects.filter(q).order_by('schedule__start_time')
    return render(request, 'personal/seller_schedule.html', {'seller_schedules': seller_schedules, 'show_past': show_past})


@login_required
@user_passes_test(is_superuser)
def generate_schedule_for_master_week():
    print("generate_schedule_for_master_week is called")
    now = timezone.now()
    start_of_week = now
    masters = list(Master.objects.all())
    workshops_count = Workshop.objects.count()  # Получаем количество мастерских

    if not masters:
        raise Exception("Нет мастеров для формирования графика")

    schedules = []
    days_to_generate = 7

    # Получаем последние расписания всех мастеров
    last_schedules = MasterSchedule.objects.values('master', 'schedule__start_time').order_by(
        'master', '-schedule__start_time'
    ).distinct('master')

    masters_last_worked = {item['master']: item['schedule__start_time'] for item in last_schedules}

    # Сортируем мастеров по последнему времени работы, ставим тех, у кого его нет, вперед
    sorted_masters = sorted(masters, key=lambda master: masters_last_worked.get(master) or datetime.min.replace(
        tzinfo=timezone.get_default_timezone()))

    # Распределяем мастеров по дням
    day_index = 0  # Индекс дня
    master_index = 0  # Индекс мастера

    for day in range(days_to_generate):
        date = start_of_week + timedelta(days=day)

        if date.date() < now.date():
            continue

        masters_on_day = 0

        while masters_on_day < workshops_count and master_index < len(sorted_masters):
            master = sorted_masters[master_index]

            # Проверяем, что мастер работает по графику 2/2
            last_master_schedules = MasterSchedule.objects.filter(master=master).order_by('-schedule__start_time')

            last_schedule = last_master_schedules.first()  # Получаем последнее расписание мастера

            if last_schedule:
                last_date = last_schedule.schedule.start_time.date()
                days_since_last_work = (date.date() - last_date).days
                if days_since_last_work < 2:
                    master_index += 1
                    continue

            schedule_start = timezone.make_aware(
                datetime(
                    date.year,
                    date.month,
                    date.day,
                    10,
                    0,
                    0
                ), timezone.get_default_timezone()
            )

            schedule_end = timezone.make_aware(
                datetime(
                    date.year,
                    date.month,
                    date.day,
                    20,
                    0,
                    0
                ), timezone.get_default_timezone()
            )
            schedules.append({
                'master': master,
                'start_time': schedule_start,
                'end_time': schedule_end,
                'duration': 10,
            })
            masters_on_day += 1
            master_index += 1

            if master_index >= len(sorted_masters):
                master_index = 0  # Переходим к началу списка
                break

    return schedules

@login_required
@user_passes_test(is_superuser)
def create_master_schedules(request):
    print("create_master_schedules is called")
    now = timezone.now()

    # Удалить существующие расписания на текущую неделю и будущие
    MasterSchedule.objects.filter(schedule__start_time__gte=now.date()).delete()
    try:
        new_schedules = generate_schedule_for_master_week()
        print("generated")
    except Exception as e:
        messages.error(request, str(e))
        return redirect('/master_schedules/')

    for schedule in new_schedules:
       # Убедитесь, что start_time и end_time - aware
        new_schedule = Schedule.objects.create(
            start_time=schedule['start_time'],
            end_time=schedule['end_time'],
            duration=schedule['duration']
        )
        MasterSchedule.objects.create(master=schedule['master'], schedule=new_schedule)
    messages.success(request, "Расписание успешно создано!")
    return redirect('master_schedules')

@login_required
@user_passes_test(is_superuser)
def master_schedules_view(request):
    masters = Master.objects.all()
    show_past = request.GET.get('show_past') == 'True'
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    q = Q()
    if date_from:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        q &= Q(schedule__start_time__date__gte=date_from)
    if date_to:
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        q &= Q(schedule__start_time__date__lte=date_to)

    master_id = request.GET.get('master')
    if master_id:
        q &= Q(master_id=master_id)
    
    if not show_past and not date_from and not date_to:
        q &= Q(schedule__start_time__date__gte=timezone.now().date())

    master_schedules = MasterSchedule.objects.filter(q).order_by('schedule__start_time')
    return render(request, 'master_schedules/master_schedules.html', {'master_schedules': master_schedules, 'masters': masters, 'show_past': show_past, 'date_from': date_from, 'date_to': date_to})

@login_required
@user_passes_test(is_superuser)
def master_schedule_add_view(request):
    masters = Master.objects.all()
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.end_time = schedule.start_time + timedelta(hours=schedule.duration)
            schedule.save()
            master_id = request.POST.get('master_id')
            master = get_object_or_404(Master, pk=master_id)
            MasterSchedule.objects.create(master=master, schedule=schedule)
            messages.success(request, "Расписание успешно добавлено!")
            return redirect('master_schedules')
    else:
        form = ScheduleForm()
    return render(request, 'master_schedules/master_schedule_create.html', {'form': form, 'masters': masters})

@login_required
@user_passes_test(is_superuser)
def master_schedule_detail_view(request, pk):
    master_schedule = get_object_or_404(MasterSchedule, pk=pk)
    return render(request, 'master_schedules/master_schedule_detail.html', {'master_schedule': master_schedule})

@login_required
@user_passes_test(is_superuser)
def master_schedule_update_view(request, pk):
    master_schedule = get_object_or_404(MasterSchedule, pk=pk)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=master_schedule.schedule)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.end_time = schedule.start_time + timedelta(hours=schedule.duration)
            schedule.save()
            messages.success(request, "Расписание успешно обновлено!")
            return redirect('master_schedules')
    else:
        form = ScheduleForm(instance=master_schedule.schedule)
    return render(request, 'master_schedules/master_schedule_update.html', {'form': form, 'master_schedule': master_schedule})

@login_required
@user_passes_test(is_superuser)
def master_schedule_delete_view(request, pk):
    master_schedule = get_object_or_404(MasterSchedule, pk=pk)
    if request.method == 'POST':
        master_schedule.delete()
        messages.success(request, "Расписание успешно удалено!")
        return redirect('master_schedules')
    return render(request, 'master_schedules/master_schedule_delete.html', {'master_schedule': master_schedule})

@login_required
@user_passes_test(is_master)
def my_master_schedule_view(request):
    try:
        master = Master.objects.get(user=request.user)
    except ObjectDoesNotExist:
         return render(request, 'personal/master_schedule.html', {'master_schedules': None})
    show_past = request.GET.get('show_past')

    q = Q(master=master)
    if not show_past:
        q &= Q(schedule__start_time__gte=timezone.now())
    
    master_schedules = MasterSchedule.objects.filter(q).order_by('schedule__start_time')
    return render(request, 'personal/master_schedule.html', {'master_schedules': master_schedules, 'show_past': show_past})





@login_required
def my_orders_view(request):
    orders = Order.objects.filter(appointment__client=request.user).order_by('purchase_date')
    now = timezone.now()
    upcoming_orders = [order for order in orders if order.appointment.start_time > now]
    archived_orders = [order for order in orders if order.appointment.start_time <= now]

    context = {
        'upcoming_orders': upcoming_orders,
        'archived_orders': archived_orders,
    }

    return render(request, 'personal/my_orders.html', context)



def booking_view(request):
    service_id = request.GET.get('service_id')
    return render(request, 'personal/booking.html', {'selected_service_id': service_id})


def get_workshops(request):
    workshops = Workshop.objects.all()
    workshop_list = []
    for workshop in workshops:
         workshop_list.append({'id': workshop.id, 'name': workshop.name, 'area': workshop.area, 'capacity': workshop.capacity})
    return JsonResponse(workshop_list, safe=False)

def get_masters(request):
    date_str = request.GET.get('date')
    time_str = request.GET.get('time')
    duration = int(request.GET.get('duration', 0))
    workshop_id = request.GET.get('workshop_id')

    if not date_str or not time_str or not duration or not workshop_id:
        return JsonResponse({'message': 'Invalid parameters'}, status=400)

    try:
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        booking_time = datetime.strptime(time_str, '%H:%M').time()
        booking_start_datetime = datetime.combine(booking_date, booking_time)
        booking_end_datetime = booking_start_datetime + timedelta(minutes=duration)
    except (ValueError, TypeError):
        return JsonResponse({'message': 'Invalid date or time format'}, status=400)

    # Получаем список занятых мастеров
    unavailable_masters = set()
    appointments = Appointment.objects.filter(
        workshop_id=workshop_id,
        start_time__lt=booking_end_datetime,
        end_time__gt=booking_start_datetime
    )
    for appointment in appointments:
        unavailable_masters.add(appointment.master_id)
    available_masters = []
    master_schedules = MasterSchedule.objects.filter(
        schedule__start_time__date=booking_date
    ).select_related('master', 'master__user', 'schedule')
    for ms in master_schedules:
        if ms.master.id not in unavailable_masters:
            available_masters.append(ms.master)
    print(available_masters)
    masters_list = [{'id': master.id, 'user': {'first_name': master.user.first_name, 'last_name': master.user.last_name}} for master in available_masters]
    return JsonResponse(masters_list, safe=False)

@login_required
def booking_view(request):
    service_id = request.GET.get('service_id')
    if not service_id:
        return HttpResponseBadRequest("Missing service_id parameter")

    selected_service = get_object_or_404(Service, id=service_id)
    context = {'selected_service': selected_service}
    return render(request, 'personal/booking.html', context)

@csrf_exempt
@login_required
def create_booking(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            service_id = data.get('service_id')
            workshop_id = data.get('workshop_id')
            booking_date = data.get('booking_date')
            booking_time = data.get('booking_time')
            master_id = data.get('master_id')
            additional_services_ids = data.get('additional_services', [])

            if not all([service_id, workshop_id, booking_date, booking_time, master_id]):
                return JsonResponse({'message': 'Missing required parameters'}, status=400)

            booking_datetime_str = f"{booking_date} {booking_time}"
            booking_datetime = datetime.strptime(booking_datetime_str, '%Y-%m-%d %H:%M')

            service = Service.objects.get(id=service_id)
            start_time = booking_datetime
            end_time = booking_datetime + timedelta(minutes=service.duration)
            workshop = Workshop.objects.get(id=workshop_id)
            master = Master.objects.get(id=master_id)


           # Проверка на занятость мастера в это время и в этой мастерской
            if Appointment.objects.filter(
                workshop=workshop,
                master=master,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists():
                return JsonResponse({'message': 'Выбранный мастер не доступен в это время.'}, status=400)

            appointment = Appointment.objects.create(
                workshop=workshop,
                master=master,
                client=request.user,
                start_time=start_time,
                end_time=end_time,
                main_service=service
            )
            order = Order.objects.create(appointment=appointment)

            for add_service_id in additional_services_ids:
                add_service = Service.objects.get(id=add_service_id)
                OrderAdditionalService.objects.create(order=order, service=add_service)

            return JsonResponse({'message': 'Order created successfully', 'order_id': order.id}, status=201)

        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=400)

    return JsonResponse({'message': 'Invalid request'}, status=400)

def get_available_times(request):
    selected_date = request.GET.get('date')
    workshop_id = request.GET.get('workshop_id')
    service_id = request.GET.get('service_id')

    if not all([selected_date, workshop_id, service_id]):
        return JsonResponse({'error': 'Date and workshop_id are required'}, status=400)

    try:
        selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
        service = Service.objects.get(id=service_id)
        workshop = Workshop.objects.get(id=workshop_id)

        start_of_day = datetime.combine(selected_date_obj, datetime.min.time())
        end_of_day = datetime.combine(selected_date_obj, datetime.max.time())

        available_times = []
        current_time = start_of_day.replace(hour=10, minute=0) # ставим начало рабочего дня в 9 утра
        end_of_day = current_time.replace(hour=20) # ставим конец рабочего дня в 9 вечера

        while current_time < end_of_day:
           end_time = current_time + timedelta(minutes=service.duration)
           if not Appointment.objects.filter(
                workshop=workshop,
                start_time__lt=end_time,
                end_time__gt=current_time
            ).exists():
               available_times.append(current_time.strftime('%H:%M'))
           current_time += timedelta(minutes=30) # ставим шаг в 30 минут

        return JsonResponse(available_times, safe=False)
    except Exception as e:
         return JsonResponse({'error': str(e)}, status=400)


def get_workshops(request):
    people_count = request.GET.get('people_count')
    service_id = request.GET.get('service_id')

    if not all([people_count, service_id]):
      return JsonResponse({'error': 'people_count and service_id is required'}, status=400)

    try:
        people_count = int(people_count)
        service = Service.objects.get(id=service_id)
        workshops = Workshop.objects.filter(capacity__gte=people_count)
        workshop_data = [
          {'id': workshop.id, 'name': workshop.name}
          for workshop in workshops
        ]
        return JsonResponse(workshop_data, safe=False)
    except Exception as e:
         return JsonResponse({'error': str(e)}, status=400)


def get_masters(request):
    workshop_id = request.GET.get('workshop_id')
    selected_date = request.GET.get('date')
    selected_time = request.GET.get('time')

    if not all([workshop_id, selected_date, selected_time]):
        return JsonResponse({'error': 'workshop_id, date, and time are required'}, status=400)

    try:
        workshop = Workshop.objects.get(pk=workshop_id)
        selected_datetime = datetime.strptime(f"{selected_date} {selected_time}", '%Y-%m-%d %H:%M')
        appointments = Appointment.objects.filter(workshop=workshop, start_time=selected_datetime)
        available_masters = Master.objects.exclude(appointment__in=appointments)

        # Фильтруем по графику работы
        available_masters = [
            master for master in available_masters
            if is_master_available_on_day(master, selected_date, selected_time)
        ]

        master_data = [{'id': m.id, 'first_name': m.user.first_name, 'last_name': m.user.last_name} for m in available_masters]
        return JsonResponse(master_data, safe=False)

    except Workshop.DoesNotExist:
        return JsonResponse({'error': 'Workshop not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def is_master_available_on_day(master, date_str, selected_time):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    schedules = MasterSchedule.objects.filter(master=master)
    
    for master_schedule in schedules:
        schedule = master_schedule.schedule
        start_time = schedule.start_time
        end_time = schedule.end_time
        selected_time_obj = datetime.strptime(selected_time, '%H:%M').time()


        schedule_date_start = datetime.combine(date_obj, start_time)
        schedule_date_end = datetime.combine(date_obj, end_time)
        selected_date_time = datetime.combine(date_obj,selected_time_obj)
        print(master.first_name)
        if  schedule_date_start <= selected_date_time <= schedule_date_end:
           return True
            
    return False
    


def get_service(request, service_id):
    """Возвращает информацию об услуге в формате JSON."""
    try:
        service = Service.objects.get(pk=service_id)
        service_data = {
            'id': service.id,
            'name': service.name,
            'price': service.price,
            'duration': service.duration,
        }
        return JsonResponse(service_data)
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)

def get_additional_services(request):
    """Возвращает список дополнительных услуг в формате JSON."""
    try:
        additional_services = Service.objects.filter(is_additional=True)  # Предполагаем, что есть поле is_additional
        services_data = [
            {
                'id': service.id,
                'name': service.name,
                'price': service.price,
            } for service in additional_services
        ]
        return JsonResponse(services_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@login_required
@user_passes_test(is_master)
def orders_list_view(request):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    client_query = request.GET.get('client')
    workshop_query = request.GET.get('workshop')
    master_query = request.GET.get('master')

    orders = Order.objects.all()

    if date_from:
        orders = orders.filter(appointment__start_time__date__gte=date_from)
    if date_to:
        orders = orders.filter(appointment__start_time__date__lte=date_to)

    if client_query:
        orders = orders.filter(appointment__client_id=client_query)
    if workshop_query:
        orders = orders.filter(appointment__workshop_id=workshop_query)
    if master_query:
         orders = orders.filter(appointment__master_id=master_query)

    # Получаем все объекты для отображения в выпадающих списках
    clients = Client.objects.all()
    workshops = Workshop.objects.all()
    masters = Master.objects.all()


    return render(request, 'orders/orders.html', {  # замените на ваш шаблон
        'orders': orders,
        'date_from': date_from,
        'date_to': date_to,
        'client': client_query,
        'workshop': workshop_query,
        'master': master_query,
        'clients': clients,
        'workshops': workshops,
        'masters': masters,
    })

def appointment_order_create_view(request):
    if request.method == 'POST':
        form = AppointmentOrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            return redirect('orders_list')
    else:
        form = AppointmentOrderForm()
    return render(request, 'orders/order_create.html', {'form': form})

@login_required
@user_passes_test(is_superuser)
def order_update_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    appointment = order.appointment

    if request.method == 'POST':
        appointment_form = AppointmentForm(request.POST, instance=appointment)
        order_form = OrderUpdateForm(request.POST, instance=order)
        formset = OrderAdditionalServiceFormSet(request.POST, instance=order)

        if appointment_form.is_valid() and order_form.is_valid() and formset.is_valid():
            appointment = appointment_form.save() # Save the Appointment before Order
            order_form.save() # Save the Order
            formset.save()
        else:
            print(appointment_form.errors)  # For debugging, if form is not valid
            print(order_form.errors)  # For debugging, if form is not valid
            print(formset.errors)
    else:
        appointment_form = AppointmentForm(instance=appointment)
        order_form = OrderUpdateForm(instance=order)
        formset = OrderAdditionalServiceFormSet(instance=order)

    context = {
        'order': order,
        'appointment_form': appointment_form,
        'order_form': order_form,
        'formset': formset,
    }
    return render(request, 'orders/order_update.html', context)


def order_detail_admin_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    additional_services = OrderAdditionalService.objects.filter(order=order)
    return render(request, 'orders/order_detail.html', {'order': order, 'additional_services': additional_services})

@login_required
@user_passes_test(is_superuser)
def order_delete_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        order.delete()
        messages.success(request, "Заказ успешно удален!")
        return redirect('orders_list')  # Перенаправляем на список заказов
    context = {'order':order}
    return render(request, 'orders/order_delete.html', context)
    order = get_object_or_404(Order, pk=id)
    if request.method == 'POST':
        order.delete()
        return redirect('orders_list')
    else:
        return render(request, 'orders/order_delete.html', {'order': order})