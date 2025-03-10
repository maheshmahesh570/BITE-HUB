import time
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect, csrf_exempt

from .models import Category,Product, CartItem, Favorite, Order
from django.db.models import Q
from django.conf import settings
import razorpay
from django.http import JsonResponse, HttpResponseRedirect


def home(request):
    query = request.GET.get('q', '').strip()  # Search query
    category_id = request.GET.get('category')  # Selected category
    min_price = request.GET.get('min_price')  # Minimum price
    max_price = request.GET.get('max_price')  # Maximum price
    sort_by = request.GET.get('sort_by', 'name')  # Default sorting by name

    # Fetch all available products
    products = Product.objects.filter(is_available=True)

    # Apply search filter (if a query is provided)
    if query:
        products = products.filter(
            Q(name__icontains=query) |  # Search by product name
            Q(description__icontains=query)  # Search by product description
        )

    # Apply category filter (if a category is selected)
    if category_id:
        products = products.filter(category_id=category_id)

    # Apply price range filter (if min_price or max_price is provided)
    if min_price:
        products = products.filter(price__gte=min_price)  # Greater than or equal to min_price
    if max_price:
        products = products.filter(price__lte=max_price)  # Less than or equal to max_price

    # Apply sorting (by name, price, or date added)
    if sort_by == 'price_asc':
        products = products.order_by('price')  # Sort by price ascending
    elif sort_by == 'price_desc':
        products = products.order_by('-price')  # Sort by price descending
    elif sort_by == 'date_newest':
        products = products.order_by('-created_at')  # Sort by newest first
    elif sort_by == 'date_oldest':
        products = products.order_by('created_at')  # Sort by oldest first
    else:
        products = products.order_by('name')  # Default: Sort by name

    # Fetch all categories for the dropdown filter
    categories = Category.objects.all()

    context = {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': int(category_id) if category_id else None,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
    }
    return render(request, 'home.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')  # Get the 'next' parameter from the query string
            if next_url:
                return redirect(next_url)  # Redirect to the original page after login
            return redirect('home')  # Default redirect to home page
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.total_price() for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')
@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('cart')

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    if request.method == 'POST':
        quantity = int(request.POST['quantity'])
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart')


@login_required
def favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Favorite.objects.get_or_create(user=request.user, product=product)
    return redirect('home')

@login_required
def favorites(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('product')
    return render(request, 'favorites.html', {'favorites': favorites})


def product_details(request, product_id):
    # Fetch the product by its ID
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_details.html', {'product': product})

@login_required
def add_to_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Favorite.objects.get_or_create(user=request.user, product=product)
    return redirect('home')

@login_required
def remove_from_favorites(request, product_id):
    favorite = get_object_or_404(Favorite, user=request.user, product_id=product_id)
    favorite.delete()
    return redirect('favorites')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'order_history.html', {'orders': orders})

@login_required
@csrf_protect
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.total_price() for item in cart_items)

    if request.method == 'POST':
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        order_amount = int(total * 100)  # Razorpay expects amount in paise
        order_currency = 'INR'

        receipt = f'order_{request.user.id}_{int(time.time())}'
        notes = {
            'email': request.user.email,
            'name': request.user.username,
        }

        razorpay_order = client.order.create({
            'amount': order_amount,
            'currency': order_currency,
            'receipt': receipt,
            'notes': notes,
            'payment_capture': 1,  # Auto-capture payments
        })

        order = Order.objects.create(
            user=request.user,
            total_amount=total,
            razorpay_order_id=razorpay_order['id']
        )
        order.items.set(cart_items)

        return render(request, 'payment.html', {
            'order': order,
            'cart_items': cart_items,
            'total': total,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'razorpay_order_id': razorpay_order['id'],
        })

    return render(request, 'checkout.html', {'cart_items': cart_items, 'total': total})


@login_required
@csrf_exempt

def verify_payment(request):
    if request.method == 'POST':
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        data = {
            'razorpay_order_id': request.POST.get('razorpay_order_id'),
            'razorpay_payment_id': request.POST.get('razorpay_payment_id'),
            'razorpay_signature': request.POST.get('razorpay_signature'),
        }



        try:
            # Verify the payment signature
            client.utility.verify_payment_signature(data)

            # Fetch the order and update its status
            order_id = request.POST.get('razorpay_order_id')
            order = Order.objects.get(razorpay_order_id=order_id)
            order.payment_id = data['razorpay_payment_id']
            order.is_paid = True
            order.save()

            # Clear the cart after successful payment
            CartItem.objects.filter(user=request.user).delete()

            # Redirect to the payment success page
            return HttpResponseRedirect(reverse('payment_success') + f'?payment_id={data["razorpay_payment_id"]}&order_id={order.id}')

        except Exception as e:
            # Handle invalid payment or verification failure
            return JsonResponse({'error': str(e)}, status=400)

    # return JsonResponse({'error': 'Invalid request'}, status=400)
    return HttpResponseRedirect(reverse('payment_success'))

@login_required
@csrf_protect
def payment_success(request):
    CartItem.objects.filter(user=request.user).delete()
    return render(request, 'payment_success.html')

@login_required
def order_details(request, order_id):
    # Fetch the order by its ID
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Calculate the total price of all items in the order
    total_price = sum(item.total_price() for item in order.items.all())

    context = {
        'order': order,
        'total_price': total_price,
    }
    return render(request, 'order_history.html', context)