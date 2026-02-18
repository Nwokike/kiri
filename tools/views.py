from django.shortcuts import render
from django.contrib.auth.decorators import login_not_required

@login_not_required
def index(request):
    return render(request, 'tools/index.html')

@login_not_required
def json_formatter(request):
    return render(request, 'tools/json_formatter.html')

@login_not_required
def regex_tester(request):
    return render(request, 'tools/regex_tester.html')

@login_not_required
def base64_converter(request):
    return render(request, 'tools/base64_converter.html')

@login_not_required
def diff_viewer(request):
    return render(request, 'tools/diff_viewer.html')

@login_not_required
def url_encoder(request):
    return render(request, 'tools/url_encoder.html')

@login_not_required
def timestamp_converter(request):
    return render(request, 'tools/timestamp_converter.html')

@login_not_required
def hash_generator(request):
    return render(request, 'tools/hash_generator.html')

@login_not_required
def uuid_generator(request):
    return render(request, 'tools/uuid_generator.html')

@login_not_required
def sql_refinery(request):
    return render(request, 'tools/sql_refinery.html')

@login_not_required
def sql_workbench(request):
    return render(request, 'tools/sql_workbench.html')

@login_not_required
def cron_generator(request):
    return render(request, 'tools/cron_generator.html')

@login_not_required
def jwt_parser(request):
    return render(request, 'tools/jwt_parser.html')

@login_not_required
def unit_converter(request):
    return render(request, 'tools/unit_converter.html')

@login_not_required
def latex_editor(request):
    return render(request, 'tools/latex_editor.html')

@login_not_required
def json_csv_converter(request):
    return render(request, 'tools/json_csv_converter.html')

@login_not_required
def image_to_base64(request):
    return render(request, 'tools/image_to_base64.html')

@login_not_required
def yaml_json_converter(request):
    return render(request, 'tools/yaml_json_converter.html')

@login_not_required
def markdown_previewer(request):
    return render(request, 'tools/markdown_previewer.html')

@login_not_required
def html_entities(request):
    return render(request, 'tools/html_entities.html')

@login_not_required
def password_generator(request):
    return render(request, 'tools/password_generator.html')

@login_not_required
def api_tester(request):
    return render(request, 'tools/api_tester.html')

@login_not_required
def data_profiler(request):
    return render(request, 'tools/data_profiler.html')

@login_not_required
def json_schema_validator(request):
    return render(request, 'tools/json_schema_validator.html')



@login_not_required
def pdf_merger(request):
    return render(request, 'tools/pdf_merger.html')

@login_not_required
def pdf_text_extractor(request):
    return render(request, 'tools/pdf_text_extractor.html')

@login_not_required
def image_resizer(request):
    return render(request, 'tools/image_resizer.html')

@login_not_required
def image_converter(request):
    return render(request, 'tools/image_converter.html')

@login_not_required
def pdf_editor(request):
    return render(request, 'tools/pdf_editor.html')

@login_not_required
def markdown_to_pdf(request):
    return render(request, 'tools/markdown_to_pdf.html')

@login_not_required
def image_to_pdf(request):
    return render(request, 'tools/image_to_pdf.html')

@login_not_required
def pdf_to_image(request):
    return render(request, 'tools/pdf_to_image.html')

@login_not_required
def pdf_splitter(request):
    return render(request, 'tools/pdf_splitter.html')

@login_not_required
def heic_to_jpg(request):
    return render(request, 'tools/heic_to_jpg.html')

@login_not_required
def image_compressor(request):
    return render(request, 'tools/image_compressor.html')

@login_not_required
def exif_viewer(request):
    return render(request, 'tools/exif_viewer.html')

@login_not_required
def ocr_tool(request):
    return render(request, 'tools/ocr_tool.html')

@login_not_required
def audio_transcriber(request):
    return render(request, 'tools/audio_transcriber.html')

@login_not_required
def qr_generator(request):
    return render(request, 'tools/qr_generator.html')
