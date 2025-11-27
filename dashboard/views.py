from django.shortcuts import render, redirect


# Create your views here.
def admin_dashboard(request):
    return render(request, 'dashboard/admindashboard.html', {
        'active': 'dashboard'
    })



