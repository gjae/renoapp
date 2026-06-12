from django.shortcuts import render
from django.http.response import HttpResponse

# Create your views here.
def view_example(request):
    return HttpResponse("{{app_name}} app is working")