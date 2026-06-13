from django.core.management.base import BaseCommand
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

class Command(BaseCommand):
    help = "Display current RenoApp URLs"

    def handle(self, *args, **options):
        """
        Executes the management command to retrieve and print all registered URL patterns.
        
        The URLs are sorted alphabetically by their route pattern. API endpoints are 
        highlighted for better readability.
        """
        resolver = get_resolver()
        urls = self.extract_urls(resolver.url_patterns)
        
        urls = sorted(urls, key=lambda x: x['pattern'])
        
        self.stdout.write(self.style.SUCCESS(f"\n{'Ruta (URL)':<60} | {'Nombre (Name)':<30} | {'Vista (View)'}"))
        self.stdout.write("-" * 120)
        
        for url in urls:
            pattern_str = url['pattern']
            if pattern_str.startswith('api/'):
                pattern_str = self.style.WARNING(f"{pattern_str:<60}")
            else:
                pattern_str = f"{pattern_str:<60}"
                
            name_str = f"{url['name']:<30}"
            self.stdout.write(f"{pattern_str} | {name_str} | {url['view']}")
            
        self.stdout.write(self.style.SUCCESS(f"\nTotal de rutas encontradas: {len(urls)}\n"))

    def extract_urls(self, urlpatterns, prefix=''):
        """
        Recursively extracts URL patterns from a list of urlpatterns or resolvers.
        
        Args:
            urlpatterns (list): A list of URLPattern or URLResolver objects.
            prefix (str, optional): The accumulated path prefix. Defaults to ''.
            
        Returns:
            list: A list of dictionaries containing 'pattern', 'name', and 'view' for each route.
        """
        urls = []
        for p in urlpatterns:
            if isinstance(p, URLPattern):
                pattern = prefix + str(p.pattern)
                pattern = pattern.replace('^', '').replace('$', '')
                
                name = p.name or ''
                
                if hasattr(p.callback, 'view_class'):
                    view_name = p.callback.view_class.__name__
                elif hasattr(p.callback, '__name__'):
                    view_name = p.callback.__name__
                else:
                    view_name = str(p.callback)
                    
                urls.append({
                    'pattern': pattern,
                    'name': name,
                    'view': view_name
                })
            elif isinstance(p, URLResolver):
                pattern = prefix + str(p.pattern)
                pattern = pattern.replace('^', '').replace('$', '')
                urls.extend(self.extract_urls(p.url_patterns, pattern))
                
        return urls
