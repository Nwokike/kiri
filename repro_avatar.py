from django.test import TestCase
from users.models import CustomUser

class AvatarSyncTest(TestCase):
    def test_avatar_prioritization(self):
        user = CustomUser(username="testuser")
        
        # Test 1: No avatars
        self.assertIsNone(user.avatar_url)
        
        # Test 2: Only Hugging Face
        user.huggingface_avatar_url = "https://huggingface.co/avatar.png"
        self.assertEqual(user.avatar_url, "https://huggingface.co/avatar.png")
        
        # Test 3: Both, GitHub prioritized
        user.github_avatar_url = "https://github.com/avatar.png"
        self.assertEqual(user.avatar_url, "https://github.com/avatar.png")
        
        # Test 4: Only GitHub
        user.huggingface_avatar_url = ""
        self.assertEqual(user.avatar_url, "https://github.com/avatar.png")
        
        # Test 5: Empty strings (handled by property)
        user.github_avatar_url = ""
        self.assertIsNone(user.avatar_url)

if __name__ == "__main__":
    import django
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kiri_project.settings")
    django.setup()
    
    from django.test.utils import get_runner
    TestRunner = get_runner(django.conf.settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["users.tests.AvatarSyncTest"])
    if failures:
        print(f"Tests failed: {failures}")
    else:
        print("Tests passed!")
