from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    path('', views.index, name='index'),
    path('json-formatter/', views.json_formatter, name='json_formatter'),
    path('regex-tester/', views.regex_tester, name='regex_tester'),
    path('base64/', views.base64_converter, name='base64_converter'),
    path('diff/', views.diff_viewer, name='diff_viewer'),
    path('url-encoder/', views.url_encoder, name='url_encoder'),
    path('timestamp/', views.timestamp_converter, name='timestamp_converter'),
    path('hash-gen/', views.hash_generator, name='hash_generator'),
    path('uuid-gen/', views.uuid_generator, name='uuid_generator'),
    path('sql-format/', views.sql_formatter, name='sql_formatter'),
    path('cron-gen/', views.cron_generator, name='cron_generator'),
    path('jwt-parser/', views.jwt_parser, name='jwt_parser'),
    path('unit-converter/', views.unit_converter, name='unit_converter'),
    path('latex-editor/', views.latex_editor, name='latex_editor'),
    path('json-to-csv/', views.json_to_csv, name='json_to_csv'),
    path('image-to-base64/', views.image_to_base64, name='image_to_base64'),
    path('yaml-json/', views.yaml_json_converter, name='yaml_json_converter'),
    path('markdown-preview/', views.markdown_previewer, name='markdown_previewer'),
    path('html-entities/', views.html_entities, name='html_entities'),
    path('password-gen/', views.password_generator, name='password_generator'),
    path('api-tester/', views.api_tester, name='api_tester'),
    path('data-profiler/', views.data_profiler, name='data_profiler'),
    path('json-schema/', views.json_schema_validator, name='json_schema_validator'),
    path('csv-to-json/', views.csv_to_json, name='csv_to_json'),
    path('pdf-merger/', views.pdf_merger, name='pdf_merger'),
    path('pdf-text-extractor/', views.pdf_text_extractor, name='pdf_text_extractor'),
    path('image-resizer/', views.image_resizer, name='image_resizer'),
    path('image-converter/', views.image_converter, name='image_converter'),
]
