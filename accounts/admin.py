from django.contrib import admin

from accounts.models import Profile, Skill, Education, Experience, Link

# Register your models here.
admin.site.register(Profile)
admin.site.register(Skill)
admin.site.register(Education)
admin.site.register(Experience)
admin.site.register(Link)
