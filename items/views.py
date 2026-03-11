from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Item
from .forms import ItemForm

def item_feed(request):
    query = request.GET.get('q')
    status_filter = request.GET.get('status')
    
    items = Item.objects.all().order_by('-date_reported')
    
    if query:
        items = items.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(location_description__icontains=query)
        )
        
    if status_filter in dict(Item.STATUS_CHOICES).keys():
        items = items.filter(status=status_filter)
        
    return render(request, 'items/feed.html', {
        'items': items, 
        'query': query,
        'current_status': status_filter
    })

def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    return render(request, 'items/item_detail.html', {'item': item})

@login_required
def report_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.reporter = request.user
            item.save()
            messages.success(request, f"Your {item.get_status_display().lower()} item report was submitted successfully.")
            return redirect('item_feed')
    else:
        form = ItemForm()
    
    return render(request, 'items/report_item.html', {'form': form})

@login_required
def edit_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    
    # Permission Check
    if request.user != item.reporter:
        messages.error(request, "You do not have permission to edit this item.")
        return redirect('item_detail', pk=item.pk)
        
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Item updated successfully.")
            return redirect('item_detail', pk=item.pk)
    else:
        form = ItemForm(instance=item)
        
    return render(request, 'items/edit_item.html', {'form': form, 'item': item})

@login_required
def delete_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    
    if request.user != item.reporter:
        messages.error(request, "You do not have permission to delete this item.")
        return redirect('item_detail', pk=item.pk)
        
    if request.method == 'POST':
        item.delete()
        messages.success(request, "Item deleted successfully.")
        return redirect('item_feed')
        
    return render(request, 'items/delete_item.html', {'item': item})
