import pytest

from cloud_tagging_cli.providers.unsupported import AzureProvider, GcpProvider


@pytest.mark.parametrize("provider_cls", [AzureProvider, GcpProvider])
def test_stub_providers_raise_not_implemented(provider_cls):
    provider = provider_cls()
    with pytest.raises(NotImplementedError):
        provider.list_resources()
    with pytest.raises(NotImplementedError):
        provider.set_tags("anything", {"k": "v"})
