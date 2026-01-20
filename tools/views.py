from django.shortcuts import render

def index(request):
    return render(request, 'tools/index.html')

def json_formatter(request):
    return render(request, 'tools/json_formatter.html')

def regex_tester(request):
    return render(request, 'tools/regex_tester.html')

def base64_converter(request):
    return render(request, 'tools/base64_converter.html')

def diff_viewer(request):
    return render(request, 'tools/diff_viewer.html')

