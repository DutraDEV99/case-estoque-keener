import os
import runpy
from pathlib import Path
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import Movimentacao, Produto


class ConfiguracaoTests(SimpleTestCase):
    def carregar(self, **ambiente):
        arquivo = Path(__file__).resolve().parent.parent / "config" / "settings.py"
        with patch.dict(os.environ, {"DJANGO_SECRET_KEY": "test-only-configuration-key", **ambiente}, clear=True):
            return runpy.run_path(str(arquivo))

    def test_instalacao_local_dispensa_mysql(self):
        config = self.carregar(DJANGO_DEBUG="True")
        self.assertEqual(config["DATABASES"]["default"]["ENGINE"], "django.db.backends.sqlite3")
        self.assertFalse(config["SECURE_SSL_REDIRECT"])
        self.assertFalse(config["SESSION_COOKIE_SECURE"])

    def test_producao_exige_https_e_postgres_ssl(self):
        config = self.carregar(DATABASE_URL="postgres://test:test@localhost/test")
        self.assertFalse(config["DEBUG"])
        self.assertTrue(config["SECURE_SSL_REDIRECT"])
        self.assertTrue(config["SESSION_COOKIE_SECURE"])
        self.assertEqual(config["DATABASES"]["default"]["OPTIONS"]["sslmode"], "require")

    def test_url_sqlite_nao_recebe_opcoes_postgres(self):
        config = self.carregar(DATABASE_URL="sqlite:///:memory:")
        self.assertNotIn("sslmode", config["DATABASES"]["default"].get("OPTIONS", {}))


@override_settings(
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
class EstoqueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("avaliador", password="Test-password-97!")
        cls.produto = Produto.objects.create(nome="Teclado", codigo="TEC-001")

    def setUp(self):
        self.client.force_login(self.user)

    def movimentar(self, tipo="ENTRADA", quantidade=5):
        return self.client.post(reverse("registrar_movimentacao"), {
            "produto": self.produto.pk, "tipo": tipo, "quantidade": quantidade,
        })

    def test_paginas_renderizam_com_marca_e_logout(self):
        for name in ("listar_produtos", "cadastrar_produto", "registrar_movimentacao", "historico_movimentacoes"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertContains(response, "DutraDEV99")
                self.assertContains(response, 'action="/logout/"')
                self.assertNotContains(response, "KEENER")
        self.assertEqual(self.client.get(reverse("editar_produto", args=[self.produto.pk])).status_code, 200)

    def test_paginas_exigem_autenticacao(self):
        self.client.logout()
        for name in ("listar_produtos", "cadastrar_produto", "registrar_movimentacao", "historico_movimentacoes"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 302)

    def test_login_e_logout(self):
        self.client.logout()
        self.assertRedirects(self.client.post(reverse("login"), {
            "username": "avaliador", "password": "Test-password-97!",
        }), reverse("listar_produtos"))
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_exige_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse("logout")).status_code, 403)

    def test_cadastro_usuario_e_senha_fraca(self):
        self.client.post(reverse("cadastrar_usuario"), {
            "username": "fraco", "password1": "123", "password2": "123",
        })
        self.assertFalse(get_user_model().objects.filter(username="fraco").exists())
        response = self.client.post(reverse("cadastrar_usuario"), {
            "username": "novo", "password1": "New-user-password-97!", "password2": "New-user-password-97!",
        })
        self.assertRedirects(response, reverse("login"))
        self.assertTrue(get_user_model().objects.get(username="novo").check_password("New-user-password-97!"))

    def test_criar_editar_e_validar_produto(self):
        self.assertRedirects(self.client.post(reverse("cadastrar_produto"), {
            "nome": "Mouse", "codigo": "MOU-001",
        }), reverse("listar_produtos"))
        self.assertRedirects(self.client.post(reverse("editar_produto", args=[self.produto.pk]), {
            "nome": "Teclado novo", "codigo": self.produto.codigo,
        }), reverse("listar_produtos"))
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.nome, "Teclado novo")
        for data in ({"nome": "Outro", "codigo": self.produto.codigo}, {"nome": "", "codigo": ""}):
            self.assertEqual(self.client.post(reverse("cadastrar_produto"), data).status_code, 200)
        self.assertEqual(Produto.objects.count(), 2)

    def test_entrada_e_saida_atualizam_saldo_e_historico(self):
        self.assertRedirects(self.movimentar(quantidade=10), reverse("historico_movimentacoes"))
        self.assertRedirects(self.movimentar("SAIDA", 3), reverse("historico_movimentacoes"))
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 7)
        self.assertEqual(Movimentacao.objects.count(), 2)
        self.assertEqual(Movimentacao.objects.first().usuario, self.user)

    def test_saida_sem_estoque_e_quantidades_invalidas(self):
        self.assertEqual(self.movimentar("SAIDA", 1).status_code, 200)
        for quantidade in (0, -1, "abc"):
            self.assertEqual(self.movimentar(quantidade=quantidade).status_code, 200)
        self.assertEqual(self.movimentar("INVALIDO").status_code, 200)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 0)
        self.assertFalse(Movimentacao.objects.exists())

    def test_produto_inativo_nao_recebe_movimentacao(self):
        self.produto.ativo = False
        self.produto.save()
        self.assertEqual(self.movimentar().status_code, 200)
        self.assertFalse(Movimentacao.objects.exists())

    def test_transacao_desfaz_saldo_se_historico_falhar(self):
        with patch.object(Movimentacao, "save", side_effect=IntegrityError("Falha simulada")):
            with self.assertRaises(IntegrityError):
                self.movimentar()
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 0)
        self.assertFalse(Movimentacao.objects.exists())

    def test_excluir_sem_historico_e_proteger_com_historico(self):
        outro = Produto.objects.create(nome="Mouse", codigo="MOUSE")
        self.assertRedirects(self.client.post(reverse("excluir_produto", args=[outro.pk])), reverse("listar_produtos"))
        self.assertFalse(Produto.objects.filter(pk=outro.pk).exists())
        self.movimentar()
        self.assertRedirects(self.client.post(reverse("excluir_produto", args=[self.produto.pk])), reverse("listar_produtos"))
        self.assertTrue(Produto.objects.filter(pk=self.produto.pk).exists())
        self.assertEqual(Movimentacao.objects.count(), 1)

    def test_status_e_metodos_http(self):
        for name in ("alternar_status_produto", "excluir_produto"):
            self.assertEqual(self.client.get(reverse(name, args=[self.produto.pk])).status_code, 405)
        self.client.post(reverse("alternar_status_produto", args=[self.produto.pk]))
        self.produto.refresh_from_db()
        self.assertFalse(self.produto.ativo)
        self.client.post(reverse("alternar_status_produto", args=[self.produto.pk]))
        self.produto.refresh_from_db()
        self.assertTrue(self.produto.ativo)
        self.assertEqual(self.client.get(reverse("editar_produto", args=[9999])).status_code, 404)

    def test_paginacao_e_filtro_de_inativos(self):
        Produto.objects.bulk_create([Produto(nome=f"Produto {i:02}", codigo=f"P{i}") for i in range(25)])
        Produto.objects.create(nome="Inativo", codigo="OFF", ativo=False)
        response = self.client.get(reverse("listar_produtos"))
        self.assertEqual(len(response.context["produtos"]), 20)
        self.assertNotContains(response, ">Inativo<")
        response = self.client.get(reverse("listar_produtos"), {"inativos": "1"})
        self.assertContains(response, "Inativo")
        self.assertContains(response, "inativos=1&amp;page=2")
        self.assertEqual(self.client.get(reverse("listar_produtos"), {"page": "abc"}).status_code, 200)

    def test_busca_historico_abrange_todas_as_paginas(self):
        Movimentacao.objects.bulk_create([
            Movimentacao(produto=self.produto, usuario=self.user, tipo="ENTRADA", quantidade=1)
            for _ in range(25)
        ])
        response = self.client.get(reverse("historico_movimentacoes"), {"q": "Teclado", "page": 2})
        self.assertEqual(len(response.context["movimentacoes"]), 5)
        self.assertContains(response, "q=Teclado&amp;page=1")
        response = self.client.get(reverse("historico_movimentacoes"), {"q": "avaliador"})
        self.assertEqual(response.context["page_obj"].paginator.count, 25)
        response = self.client.get(reverse("historico_movimentacoes"), {"q": "inexistente"})
        self.assertEqual(response.context["page_obj"].paginator.count, 0)

    def test_admin_preserva_historico(self):
        self.assertTrue(admin.site.is_registered(Produto))
        model_admin = admin.site._registry[Movimentacao]
        request = self.client.request().wsgi_request
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request))
