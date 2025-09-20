from django.shortcuts import render
from django.contrib.auth.decorators import login_required



def index(request):
    template_data = {}
    return render(request, "home/index.html", {"template_data": template_data})

