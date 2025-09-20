from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout


# Create your views here.
def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # save user
            auth_login(request, user)  # log the user in
            return redirect("home.index")  # redirect after signup
    else:
        form = UserCreationForm()

    return render(request, "accounts/signup.html", {"form": form})


def login(request):
    if request.user.is_authenticated:
        return redirect("home.index")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect("home.index")

    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout(request):
    auth_logout(request)
    return redirect("home.index")
