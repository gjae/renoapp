from reno.router import api

# Register controllers if exists inside the app 
# only class reference
controllers = []

# Create your views here.
@api.get("/{{app_name}}")
async def view_example(request):
    return {"message": "Hello world"}

