from django.contrib import admin

from .models import Movimentacao, Produto


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "codigo", "quantidade", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "codigo")
    readonly_fields = ("quantidade",)


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ("produto", "tipo", "quantidade", "usuario", "data")
    list_filter = ("tipo", "data")
    search_fields = ("produto__nome", "produto__codigo", "usuario__username")
    list_select_related = ("produto", "usuario")

    # O histórico deve acompanhar o saldo; alterações passam pelo fluxo de estoque.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
