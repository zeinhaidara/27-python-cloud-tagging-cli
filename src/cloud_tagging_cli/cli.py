"""Click entry point: `cloud-tag check` and `cloud-tag apply`."""

from __future__ import annotations

import sys

import click

from cloud_tagging_cli.config import ConfigError, load_config
from cloud_tagging_cli.core import apply_resources, check_resources
from cloud_tagging_cli.provider import TaggingProvider
from cloud_tagging_cli.providers.aws import AwsTaggingProvider, build_client
from cloud_tagging_cli.providers.unsupported import AzureProvider, GcpProvider

PROVIDER_CHOICES = ("aws", "azure", "gcp")


def _build_provider(name: str, region: str) -> TaggingProvider:
    if name == "aws":
        return AwsTaggingProvider(build_client(region))
    if name == "azure":
        return AzureProvider()
    if name == "gcp":
        return GcpProvider()
    raise click.UsageError(f"unknown provider: {name}")


@click.group()
def main() -> None:
    """Standardize and bulk-update resource tags across clouds."""


@main.command()
@click.option("--provider", "provider_name", type=click.Choice(PROVIDER_CHOICES), default="aws")
@click.option("--region", default="us-east-1", show_default=True)
@click.option("--config", "config_path", required=True, type=click.Path(exists=True))
def check(provider_name: str, region: str, config_path: str) -> None:
    """Report resources that do not conform to the standard-tags config."""
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    provider = _build_provider(provider_name, region)
    reports = check_resources(provider, config)

    if not reports:
        click.echo("all resources conform to the standard-tags config")
        return

    for report in reports:
        click.echo(f"{report.resource_id}:")
        for violation in report.violations:
            click.echo(f"  [{violation.kind}] {violation.key}: {violation.detail}")

    click.echo(f"\n{len(reports)} non-conforming resource(s)")
    sys.exit(1)


@main.command()
@click.option("--provider", "provider_name", type=click.Choice(PROVIDER_CHOICES), default="aws")
@click.option("--region", default="us-east-1", show_default=True)
@click.option("--config", "config_path", required=True, type=click.Path(exists=True))
@click.option("--apply", "do_apply", is_flag=True, default=False, help="Actually write tags.")
def apply(provider_name: str, region: str, config_path: str, do_apply: bool) -> None:
    """Bring resources into compliance. Dry-run unless --apply is given."""
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    provider = _build_provider(provider_name, region)
    results = apply_resources(provider, config, apply=do_apply)

    mode = "applying" if do_apply else "dry-run (pass --apply to write changes)"
    click.echo(f"mode: {mode}")

    changed = [r for r in results if not r.is_noop]
    unfixable_total = 0
    for result in changed:
        verb = "applied" if do_apply else "would apply"
        click.echo(f"{result.resource_id}: {verb} {result.applied_tags}")

    for result in results:
        for violation in result.unfixable:
            unfixable_total += 1
            click.echo(
                f"{result.resource_id}: [{violation.kind}] {violation.key}: {violation.detail}"
            )

    compliant = len(results) - len(changed)
    click.echo(f"\n{len(changed)} resource(s) changed, {compliant} already compliant")

    if unfixable_total:
        click.echo(f"{unfixable_total} violation(s) require manual fixing (no default configured)")
        sys.exit(1)


if __name__ == "__main__":
    main()
