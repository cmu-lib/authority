from django.contrib import admin
import entity.models
import authority.models

admin.site.site_header = "CMU Libraries Authority Administration"
admin.site.site_title = "CMU Libraries Authority Administration"
admin.site.index_title = (
    "Welcome to the CMU Libraries Authority adminstration interface"
)


class AuthorityAdmin(admin.ModelAdmin):
    model = authority.models.Authority


admin.site.register(authority.models.Authority, AuthorityAdmin)


class CloseMatchAdmin(admin.ModelAdmin):
    model = authority.models.CloseMatch


admin.site.register(authority.models.CloseMatch, CloseMatchAdmin)


class NameInline(admin.TabularInline):
    model = entity.models.Name
    extra = 1


class CloseMatchInline(admin.TabularInline):
    model = authority.models.CloseMatch
    extra = 1


class PersonAdmin(admin.ModelAdmin):
    model = entity.models.Person
    search_fields = ["pref_label"]
    list_display = [
        "pref_label",
        "birth_early",
        "birth_late",
        "death_early",
        "death_late",
        "viaf_match",
        "lcnaf_match",
    ]
    inlines = [NameInline, CloseMatchInline]


admin.site.register(entity.models.Person, PersonAdmin)


class NameAdmin(admin.ModelAdmin):
    model = entity.models.Name
    list_display = ["label", "language", "name_of"]


admin.site.register(entity.models.Name, NameAdmin)