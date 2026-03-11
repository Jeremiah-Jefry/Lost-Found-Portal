from django.shortcuts import render
from items.models import Item

def index(request):
    total_lost = Item.objects.filter(status='LOST').count()
    total_found = Item.objects.filter(status='FOUND').count()
    
    my_items = None
    if request.user.is_authenticated:
        my_items = Item.objects.filter(reporter=request.user).order_by('-date_reported')
        
    context = {
        'total_lost': total_lost,
        'total_found': total_found,
        'my_items': my_items,
    }
    return render(request, 'dashboard/index.html', context)
