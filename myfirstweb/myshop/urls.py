#from django.contrib import admin 
#from django.urls import path, include

#urlpatterns = [
#path( 'admin/', admin.site.urls),
#path('', include('myshop.urls'))
#]

from django.urls import path 
from views import Home

urlpatterns = [
path('', Home),
]