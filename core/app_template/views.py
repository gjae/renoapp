from ninja_extra import NinjaExtraAPI

api = NinjaExtraAPI()

# Create your views here.
@api.get("/{{app_name}}")
async def view_example(request):
    return {"message": "Hello world"}