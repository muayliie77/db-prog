from django.shortcuts import render
from django.http import HttpResponse

#def Home (request) :
    #return HttpResponse('<h1 > Hello Django : MyShop </h1>')

def Home (request) :
    return render(request, 'myshop_template/home.html')