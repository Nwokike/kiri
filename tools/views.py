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

def url_encoder(request):
    return render(request, 'tools/url_encoder.html')

def timestamp_converter(request):
    return render(request, 'tools/timestamp_converter.html')

def hash_generator(request):
    return render(request, 'tools/hash_generator.html')

def uuid_generator(request):
    return render(request, 'tools/uuid_generator.html')

def sql_formatter(request):
    return render(request, 'tools/sql_formatter.html')

def cron_generator(request):
    return render(request, 'tools/cron_generator.html')

def jwt_parser(request):
    return render(request, 'tools/jwt_parser.html')

def unit_converter(request):
    return render(request, 'tools/unit_converter.html')

def latex_editor(request):
    return render(request, 'tools/latex_editor.html')

def json_to_csv(request):
    return render(request, 'tools/json_to_csv.html')

def image_to_base64(request):
    return render(request, 'tools/image_to_base64.html')

def yaml_json_converter(request):
    return render(request, 'tools/yaml_json_converter.html')

def markdown_previewer(request):
    return render(request, 'tools/markdown_previewer.html')

def html_entities(request):
    return render(request, 'tools/html_entities.html')

def password_generator(request):
    return render(request, 'tools/password_generator.html')

def api_tester(request):
    return render(request, 'tools/api_tester.html')

def data_profiler(request):
    return render(request, 'tools/data_profiler.html')

def json_schema_validator(request):
    return render(request, 'tools/json_schema_validator.html')

def csv_to_json(request):
    return render(request, 'tools/csv_to_json.html')

def pdf_merger(request):
    return render(request, 'tools/pdf_merger.html')

def pdf_text_extractor(request):
    return render(request, 'tools/pdf_text_extractor.html')

def image_resizer(request):
    return render(request, 'tools/image_resizer.html')

def image_converter(request):
    return render(request, 'tools/image_converter.html')

