from app.database.db import get_active_service_categories, get_active_services_with_category


categories = get_active_service_categories()
services = get_active_services_with_category()

services_by_category = {}

for category in categories:
    services_by_category[category['slug']] = []

for service in services:
    category_slug = service['category_slug']
    services_by_category[category_slug].append(service)

print(services_by_category)