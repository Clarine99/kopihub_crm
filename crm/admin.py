from django.contrib import admin

from .models import Customer, Membership, ProgramSettings, Stamp, StampCycle

admin.site.register(Customer)
admin.site.register(Membership)
admin.site.register(StampCycle)
admin.site.register(Stamp)
admin.site.register(ProgramSettings)
