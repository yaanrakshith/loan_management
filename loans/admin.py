from django.contrib import admin
from .models import Loan, Installment, LoanHistory


class InstallmentInline(admin.TabularInline):
    model = Installment
    extra = 0
    readonly_fields = ('installment_number', 'due_date',
                       'amount', 'principal_component', 'interest_component')


class LoanHistoryInline(admin.TabularInline):
    model = LoanHistory
    extra = 0
    readonly_fields = ('action', 'details', 'performed_by', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class LoanAdmin(admin.ModelAdmin):
    list_display = ('loan_id', 'user', 'amount', 'tenure',
                    'interest_rate', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('loan_id', 'user__email')
    readonly_fields = ('loan_id', 'created_at', 'updated_at')
    inlines = [InstallmentInline, LoanHistoryInline]


class InstallmentAdmin(admin.ModelAdmin):
    list_display = ('loan', 'installment_number',
                    'due_date', 'amount', 'status')
    list_filter = ('status', 'due_date')
    search_fields = ('loan__loan_id',)
    readonly_fields = ('loan', 'installment_number', 'due_date',
                       'amount', 'principal_component', 'interest_component')


class LoanHistoryAdmin(admin.ModelAdmin):
    list_display = ('loan', 'action', 'performed_by', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('loan__loan_id',)
    readonly_fields = ('loan', 'action', 'details',
                       'performed_by', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Loan, LoanAdmin)
admin.site.register(Installment, InstallmentAdmin)
admin.site.register(LoanHistory, LoanHistoryAdmin)
