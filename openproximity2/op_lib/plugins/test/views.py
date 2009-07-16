from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello World, I'm test plugin")
