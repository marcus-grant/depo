from django.shortcuts import render


# Create your views here.
def web_index(request):
    if request.method == "POST":
        content = request.POST.get("content")
        # TODO: Implement
        return render(request, "index.html", {"content": content})
    else:
        return render(request, "index.html")
