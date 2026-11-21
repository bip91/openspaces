from engine.models import Event, Typing
from engine.services.create import create_object
from engine.services.typing import set_typing


def test_set_typing_creates_typing(space, table_type, layer_fonctionnel, user):
    obj = create_object(space, table_type, {"name": "commande"}, author=user)

    typing = set_typing(obj, layer_fonctionnel, table_type, author=user)

    assert Typing.objects.filter(pk=typing.pk).exists()
    assert typing.object == obj
    assert typing.layer == layer_fonctionnel
    assert typing.type == table_type


def test_set_typing_is_idempotent(space, table_type, layer_fonctionnel, user):
    obj = create_object(space, table_type, {"name": "commande"}, author=user)

    first = set_typing(obj, layer_fonctionnel, table_type, author=user)
    second = set_typing(obj, layer_fonctionnel, table_type, author=user)

    assert first.pk == second.pk
    assert Typing.objects.filter(object=obj, layer=layer_fonctionnel, type=table_type).count() == 1
    assert Event.objects.filter(object=obj, nature="typed").count() == 1
