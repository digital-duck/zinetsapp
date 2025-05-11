import click

@click.command()
@click.option('--use-cache/--no-cache', default=True,
              help='Whether to use cache (default: True)')
def demo(use_cache):
    """Demo how Click boolean flags work."""
    click.echo(f"use_cache value: {use_cache} (type: {type(use_cache).__name__})")
    
    if use_cache:
        click.echo("Cache is ENABLED")
    else:
        click.echo("Cache is DISABLED")

if __name__ == '__main__':
    demo()