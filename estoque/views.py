
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from .models import Movimentacao, Produto


# FORMULÁRIO DE PRODUTOS
class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ["nome", "codigo"]

    def clean_codigo(self):
        codigo = self.cleaned_data.get("codigo", "").strip()

        if not codigo:
            raise forms.ValidationError("Informe o código do produto.")

        if Produto.objects.filter(codigo=codigo).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError(
                "Já existe um produto com esse código."
            )

        return codigo


# FORMULÁRIO DE MOVIMENTAÇÕES
class MovimentacaoForm(forms.ModelForm):
    class Meta:
        model = Movimentacao
        fields = ["produto", "tipo", "quantidade"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["produto"].queryset = Produto.objects.filter(
            ativo=True
        ).order_by("nome")

        self.fields["quantidade"].min_value = 1
        self.fields["quantidade"].widget.attrs["min"] = 1

    def clean_quantidade(self):
        quantidade = self.cleaned_data["quantidade"]

        if quantidade < 1:
            raise forms.ValidationError(
                "Informe uma quantidade maior que zero."
            )

        return quantidade


# LISTAR PRODUTOS
@login_required
def listar_produtos(request):
    produtos = Produto.objects.order_by("nome")

    return render(
        request,
        "estoque/produtos.html",
        {"produtos": produtos},
    )


# CADASTRAR PRODUTO
@login_required
def cadastrar_produto(request):
    if request.method == "POST":
        formulario = ProdutoForm(request.POST)

        if formulario.is_valid():
            formulario.save()
            messages.success(
                request,
                "Produto cadastrado com sucesso!"
            )
            return redirect("listar_produtos")
    else:
        formulario = ProdutoForm()

    return render(
        request,
        "estoque/cadastrar_produto.html",
        {"formulario": formulario},
    )


# EDITAR PRODUTO
@login_required
def editar_produto(request, produto_id):
    produto = get_object_or_404(
        Produto,
        pk=produto_id,
    )

    if request.method == "POST":
        formulario = ProdutoForm(
            request.POST,
            instance=produto,
        )

        if formulario.is_valid():
            formulario.save()
            messages.success(
                request,
                "Produto atualizado com sucesso!"
            )
            return redirect("listar_produtos")
    else:
        formulario = ProdutoForm(instance=produto)

    return render(
        request,
        "estoque/editar_produto.html",
        {
            "formulario": formulario,
            "produto": produto,
        },
    )


# EXCLUIR PRODUTO
@login_required
def excluir_produto(request, produto_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    produto = get_object_or_404(
        Produto,
        pk=produto_id,
    )

    try:
        produto.delete()
        messages.success(
            request,
            "Produto excluído com sucesso!"
        )

    except ProtectedError:
        messages.error(
            request,
            "Este produto possui movimentações e não pode "
            "ser excluído. Você pode desativá-lo."
        )

    return redirect("listar_produtos")


# ATIVAR OU DESATIVAR PRODUTO
@login_required
def alternar_status_produto(request, produto_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    produto = get_object_or_404(
        Produto,
        pk=produto_id,
    )

    produto.ativo = not produto.ativo
    produto.save(update_fields=["ativo"])

    if produto.ativo:
        messages.success(
            request,
            "Produto ativado com sucesso!"
        )
    else:
        messages.success(
            request,
            "Produto desativado com sucesso!"
        )

    return redirect("listar_produtos")


# CADASTRAR USUÁRIO
def cadastrar_usuario(request):
    if request.method == "POST":
        formulario = UserCreationForm(request.POST)

        if formulario.is_valid():
            formulario.save()
            return redirect("login")
    else:
        formulario = UserCreationForm()

    return render(
        request,
        "registration/cadastro.html",
        {"formulario": formulario},
    )


# REGISTRAR ENTRADAS E SAÍDAS
@login_required
def registrar_movimentacao(request):
    if request.method == "POST":
        formulario = MovimentacaoForm(request.POST)

        if formulario.is_valid():
            with transaction.atomic():
                produto = Produto.objects.select_for_update().get(
                    pk=formulario.cleaned_data["produto"].pk
                )

                tipo = formulario.cleaned_data["tipo"]
                quantidade = formulario.cleaned_data["quantidade"]

                if not produto.ativo:
                    formulario.add_error(
                        "produto",
                        "Este produto está desativado."
                    )

                elif tipo == "SAIDA" and quantidade > produto.quantidade:
                    formulario.add_error(
                        "quantidade",
                        f"Estoque insuficiente. Disponível: "
                        f"{produto.quantidade} unidade(s)."
                    )

                else:
                    if tipo == "ENTRADA":
                        produto.quantidade += quantidade
                    else:
                        produto.quantidade -= quantidade

                    produto.save(
                        update_fields=["quantidade"]
                    )

                    movimentacao = formulario.save(
                        commit=False
                    )
                    movimentacao.produto = produto
                    movimentacao.usuario = request.user
                    movimentacao.save()

                    messages.success(
                        request,
                        "Movimentação registrada com sucesso!"
                    )

                    return redirect(
                        "historico_movimentacoes"
                    )
    else:
        formulario = MovimentacaoForm()

    return render(
        request,
        "estoque/movimentar.html",
        {"formulario": formulario},
    )


# HISTÓRICO DE MOVIMENTAÇÕES
@login_required
def historico_movimentacoes(request):
    movimentacoes = (
        Movimentacao.objects
        .select_related("produto", "usuario")
        .order_by("-data", "-id")
    )

    return render(
        request,
        "estoque/historico.html",
        {"movimentacoes": movimentacoes},
    )
