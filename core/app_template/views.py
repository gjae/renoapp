from reno.router import api

# Register controllers if exists inside the app 
# only class reference
controllers = []

api.set_prefix("{{app_name}}")

# Create your views here.
@api.get("/")
async def view_example(request):
    return {"message": "Hello world"}

