from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='neo').exists():
    User.objects.create_user('neo', 'neo@kiri.ng', 'neomatrix')
    print("User neo created")
else:
    print("User neo already exists")
