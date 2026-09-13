from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from .forms import RegistrationForm,RatingForm
from . import models
from . import forms
from django.db.models import Q,Max,Min,Avg
# Create your views here.

# Manual User Authentication
def login_view(request):
    if request.method == 'POST':
       username = request.POST.get('username')
       password = request.POST.get('password')

       user = authenticate(request, username=username,password=password)

       if user is not None:
           login(request, user)
           messages.success(request,'Login Successful!')
           redirect
       else:
           messages.error(request, "invalid username or password")
    return render(request, '')

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm()
        if form.is_valid():
           user = form.save()
           login(request, user)
           messages.success(request,'Registration Successful!')
           return redirect('')
    else:
        form = RegistrationForm()
    return render(request,'',{'form':form})

def logout_view(request):
    logout(request)
    return render('')

# homepage
def home(request):
    featured_products = models.Product.objects.filter(available=True).order_by('-created_at')[:8] # descending order
    categories = models.Category.objects.all()
    return render(request,'',{'featured_product':featured_products,'categories':categories})

def product_list(request,category_slug = None):
    category = None
    categories = models.Category.objects.all()
    products = models.Product.objects.all()

    if category_slug:
        category = get_object_or_404(models.Category,category_slug)
        products = products.filter(category = category)

    min_price = products.aaggregate(Min('price'))['price_min']
    max_price = products.aaggregate(Max('price'))['price_max']

    if request.GET.get('min_price'):
        products = products.filter(price__gte=request.GET.get('min_price'))

    if request.GET.get('max_price'):
        products = products.filter(price__lte=request.GET.get('max_price'))

    if request.GET.get('rating'):
            products = products.annotate(avg_rating = Avg('ratings__rating')).filter(avg_rating=request.GET.get('rating'))

    if request.GET.get('search'):
        query = request.GET.get('search')
        products = products.filter(
            Q(name__icontains = query) |
            Q(description__icontains = query) |
            Q(category_name__icontains = query)
        )
    return render(request,'',{
        'category':category,
        'categories':categories,
        'products':products,
        'min_price':min_price,
        'max_price':max_price
    })

# product details page
def product_detail(request,slug):
    product = get_object_or_404(models.Product,slug=slug,available=True)
    related_products = models.Product.objects.filter(category = product.category).exclude(id=product.id)

    user_rating = None

    if request.user.is_authenticated:
        try:
            user_rating = models.Rating.objects.get(product=product,user=request.user)
        except models.Rating.DoesNotExist:
              pass
    rating_form = RatingForm(instance=user_rating)
    return render(request,'',{
        'product':product,
        'related_products':related_products,
        'user_rating':user_rating,
        'rating_form':rating_form
    })

def rate_product(request,product_id):
    product = get_object_or_404(models.Product,id=product.id)

    ordered_items = models.OrderItem.objects.filter(
        order__user = request.user,
        product = product,
        order__paid = True
    )

    if not ordered_items.exists():
        messages.warning(request, 'You can only rate products you have purchased')
        return redirect('')
    try:
        rating = models.Rating.objects.get(product=product,user = request.user)
    except models.Rating.DoesNotExist:
        rating = None
    if request.method == 'POST':
        form = RatingForm(request.POST, instance=rating)
        if form.is_valid():
           rating = form.save(commit=False)
           rating.product = product
           rating.user = request.user
           rating.save()
           return redirect('')
    else:
        form = RatingForm(instance=rating)
    return render(request,'',{
        'form':form,
        'product':product
    })

def cart_add(request,product_id):
    product = get_object_or_404(models.Product,id=product_id)

    try:
        cart = models.Cart.objects.get(user=request.user)
    except:
        cart = models.Cart.objects.create(user = request.user)

    try:
        cart_item = models.CartItem.objects.get(cart=cart,product=product)
        cart_item.quantity += 1
        cart_item.save()
    except models.CartItem.DoesNotExist:
        models.CartItem.objects.create(cart=cart,product=product,quantity = 1)

    messages.success(request,f"{product.name} has been added to your cart!")
    return redirect(request,'')

def cart_update(request,product_id):
    cart = get_object_or_404(models.Cart,user = request.user)
    product = get_object_or_404(models.Product,product_id)
    cart_item = get_object_or_404(models.CartItem,cart=cart,product=product)

    quantity = int(request.POST.get('quantity',1))

    if quantity <= 0:
       cart_item.delete()
       messages.success(request,f'{product.name} has been delete from your cart')
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request,f'Cart updated successfully!!')
    return redirect('')

def cart_remove(request,product_id):
    cart = get_object_or_404(models.Cart,user = request.user)
    product = get_object_or_404(models.Product,id = product_id)
    cart_item = get_object_or_404(models.CartItem,cart=cart,product=product)

    cart_item.delete()
    messages.success(request,f'{product.name} has been deleted from your cart')
    return redirect('')

def cart_detail(request):
    try:
        cart = models.Cart.objects.get(user = request.user)
    except models.Cart.DoesNotExist:
        cart = models.Cart.objects.create(user = request.user)
    return render(request,'',{'cart':cart})

# Product->Cart Item -> Order Item
def checkout(request):
    try:
        cart = models.Cart.objects.get(user = request.user)
        if not cart.items.existes():
            messages.warning(request,'your cart is empty')
            return redirect('')
    except models.Cart.DoesNotExist:
            messages.warning(request,'your cart is empty')
            return redirect('')
    if request.method == 'POST':
        form = forms.CheckoutForm(request.POST)
        if form.is_valid():
           order = form.save(commit=False)
           order.user = request.user
           order.save()

           for item in cart.items.object.all():
               models.OrderItem.objects.create(
                   order = order,
                   product = item.product,
                   price = item.product.price,
                   quantity = item.quantity
               )
           cart.items.all().delete()
           request.session['order_id'] = order.id
           return redirect('')
    else:
        form = forms.CheckoutForm()
    return render(request,'',{
        'cart':cart,
        'form':form
    })

#payment related
def payment_success(request,order_id):
    order = get_object_or_404(models.Order,id = order_id,user = request.user)
    order.paid = True
    order.status = 'processing'
    order.transaction_id = order.id
    order.save()
    order_items = order.order_items.all()
    for item in order_items:
        product = item.product
        product.stock -= item. quantity

        if product.stock < 0 :
            product.stock = 0
        product.save()

    messages.success(request,'payment successful!')
    return render(request,'',{'order':order})

def payment_fail(request, order_id):
    order = get_object_or_404(models.Order,id = order_id, user = request.user)
    order.status = 'cancelled'
    order.save()
    return redirect('')

def payment_cancelled(request, order_id):
    order = get_object_or_404(models.Order,id = order_id, user = request.user)
    order.status = 'cancelled'
    order.save()
    return redirect('')
