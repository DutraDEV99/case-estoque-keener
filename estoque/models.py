
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Produto(models.Model):
    nome = models.CharField(max_length=120)
    codigo = models.CharField(max_length=40, unique=True)
    quantidade = models.PositiveIntegerField(
        default=0,
        editable=False,
    )
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Movimentacao(models.Model):
    TIPOS = [
        ("ENTRADA", "Entrada"),
        ("SAIDA", "Saída"),
    ]

    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name="movimentacoes",
    )
    tipo = models.CharField(max_length=7, choices=TIPOS)
    quantidade = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data", "-id"]

    def __str__(self):
        return (
            f"{self.get_tipo_display()} — "
            f"{self.produto.nome}: {self.quantidade}"
        )
