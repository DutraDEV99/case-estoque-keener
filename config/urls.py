
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView

from estoque.views import (
    listar_produtos,
    cadastrar_produto,
    cadastrar_usuario,
    registrar_movimentacao,
    historico_movimentacoes,
    editar_produto,
    excluir_produto,
    alternar_status_produto,
)

urlpatterns = [
    # Página inicial
    path(
        "",
        RedirectView.as_view(
            pattern_name="login",
            permanent=False,
        ),
        name="home",
    ),

    # Administração
    path("admin/", admin.site.urls),

    # Autenticação
    path(
        "login/",
        auth_views.LoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path(
        "cadastro/",
        cadastrar_usuario,
        name="cadastrar_usuario",
    ),

    # Produtos
    path(
        "produtos/",
        listar_produtos,
        name="listar_produtos",
    ),
    path(
        "produtos/cadastrar/",
        cadastrar_produto,
        name="cadastrar_produto",
    ),
    path(
        "produtos/<int:produto_id>/editar/",
        editar_produto,
        name="editar_produto",
    ),
    path(
        "produtos/<int:produto_id>/excluir/",
        excluir_produto,
        name="excluir_produto",
    ),
    path(
        "produtos/<int:produto_id>/status/",
        alternar_status_produto,
        name="alternar_status_produto",
    ),

    # Movimentações
    path(
        "movimentar/",
        registrar_movimentacao,
        name="registrar_movimentacao",
    ),
    path(
        "historico/",
        historico_movimentacoes,
        name="historico_movimentacoes",
    ),
]
